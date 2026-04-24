from flask import Flask, render_template, flash, redirect, url_for, request
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        return User(row)
    return None


class User:
    def __init__(self, row):
        self.row = row
        self.id = row["id"]
        self.name = row["name"]
        self.email = row["email"]
        self.password_hash = row["password_hash"]

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.row["id"])


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    form = RegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password_hash = generate_password_hash(form.password.data)

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            db.commit()
        except Exception:
            flash("An account with that email already exists.", "error")
            return render_template("register.html", form=form)

        flash("Account created! Please sign in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


class RegistrationForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2)])
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Create account")

    def validate_email(self, email):
        db = get_db()
        cur = db.execute("SELECT id FROM users WHERE email = ?", (email.data,))
        if cur.fetchone():
            raise ValidationError("An account with that email already exists.")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            login_user(User(user))
            flash("Welcome back!", "success")
            return redirect(url_for("profile"))

        flash("Invalid email or password.", "error")

    return render_template("login.html", form=form)


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    db = get_db()

    # User info
    cur = db.execute("SELECT created_at FROM users WHERE id = ?", (current_user.id,))
    row = cur.fetchone()
    member_since = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")

    # Transactions (ordered by date desc, limit 10)
    cur = db.execute(
        "SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 10",
        (current_user.id,)
    )
    transactions = [dict(row) for row in cur.fetchall()]

    # Stats — total_spent and transaction_count
    cur = db.execute(
        "SELECT SUM(amount) as total, COUNT(*) as count FROM expenses WHERE user_id = ?",
        (current_user.id,)
    )
    stats_row = cur.fetchone()
    total_spent = stats_row["total"] or 0
    transaction_count = stats_row["count"] or 0

    # Top category
    cur = db.execute(
        "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC LIMIT 1",
        (current_user.id,)
    )
    top_row = cur.fetchone()
    top_category = top_row["category"] if top_row else "None"

    # Category breakdown with percentages
    cur = db.execute(
        "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC",
        (current_user.id,)
    )
    category_rows = cur.fetchall()
    grand_total = sum(r["total"] for r in category_rows) or 1
    categories = [
        {"name": r["category"], "total": r["total"], "percentage": round(r["total"] / grand_total * 100)}
        for r in category_rows
    ]

    context = {
        "user": {
            "name": current_user.name,
            "email": current_user.email,
            "member_since": member_since
        },
        "stats": {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category
        },
        "transactions": transactions,
        "categories": categories
    }
    return render_template("profile.html", **context)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
