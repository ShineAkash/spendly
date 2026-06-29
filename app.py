from flask import Flask, render_template, flash, redirect, url_for, request, abort
from datetime import datetime, date as date_cls
from flask_wtf import FlaskForm
from flask_wtf.csrf import generate_csrf
from wtforms import StringField, PasswordField, SubmitField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database.db import get_db, init_db, seed_db, add_expense as db_add_expense, update_expense as db_update_expense, delete_expense as db_delete_expense
import sqlite3

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"

# Make `{{ csrf_token() }}` available as a Jinja global so standalone (non-FlaskForm) forms
# can include a CSRF input. Existing FlaskForm-based forms keep using `form.hidden_tag()`.
app.jinja_env.globals["csrf_token"] = generate_csrf

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

    # Date filtering logic
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    valid_start = None
    valid_end = None

    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            valid_start = start_date
        except ValueError:
            pass

    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
            valid_end = end_date
        except ValueError:
            pass

    def get_filter_clause(base_query):
        params = [current_user.id]
        query = f"{base_query} WHERE user_id = ?"
        if valid_start:
            query += " AND date >= ?"
            params.append(valid_start)
        if valid_end:
            query += " AND date <= ?"
            params.append(valid_end)
        return query, params

    # User info
    cur = db.execute("SELECT created_at FROM users WHERE id = ?", (current_user.id,))
    row = cur.fetchone()
    member_since = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")

    # Transactions (ordered by date desc, limit 10)
    base_tx_query = "SELECT id, date, description, category, amount FROM expenses"
    tx_query, tx_params = get_filter_clause(base_tx_query)
    tx_query += " ORDER BY date DESC LIMIT 10"
    cur = db.execute(tx_query, tx_params)
    transactions = [dict(row) for row in cur.fetchall()]

    # Stats — total_spent and transaction_count
    base_stats_query = "SELECT SUM(amount) as total, COUNT(*) as count FROM expenses"
    stats_query, stats_params = get_filter_clause(base_stats_query)
    cur = db.execute(stats_query, stats_params)
    stats_row = cur.fetchone()
    total_spent = stats_row["total"] or 0
    transaction_count = stats_row["count"] or 0

    # Top category (lifetime, ignores date filter)
    cur = db.execute(
        "SELECT category, SUM(amount) as total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY total DESC LIMIT 1",
        (current_user.id,)
    )
    top_row = cur.fetchone()
    top_category = top_row["category"] if top_row else "None"

    # Category breakdown (lifetime, ignores date filter)
    cur = db.execute(
        "SELECT category, SUM(amount) as total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY total DESC",
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


@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")


class ExpenseForm(FlaskForm):
    amount = DecimalField(
        "Amount",
        places=2,
        validators=[DataRequired(), NumberRange(min=0.01, max=1_000_000)]
    )
    category = SelectField("Category", choices=[
        ("Food", "Food"),
        ("Transport", "Transport"),
        ("Bills", "Bills"),
        ("Health", "Health"),
        ("Entertainment", "Entertainment"),
        ("Shopping", "Shopping"),
        ("Other", "Other")
    ], validators=[DataRequired()])
    date = DateField("Date", format="%Y-%m-%d", validators=[DataRequired()],
                     default=date_cls.today)
    description = StringField("Description", validators=[Length(max=200)])
    submit = SubmitField("Add Expense")

    def validate_date(self, field):
        if field.data and field.data > date_cls.today():
            raise ValidationError("Date cannot be in the future.")


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    form = ExpenseForm()

    if form.validate_on_submit():
        try:
            db_add_expense(
                current_user.id,
                float(form.amount.data),
                form.category.data,
                form.date.data.isoformat(),
                form.description.data
            )
        except sqlite3.Error:
            app.logger.exception("add_expense: database insert failed")
            flash("Could not save the expense. Please try again.", "error")
            return render_template("add_expense.html", form=form)

        flash("Expense added successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("add_expense.html", form=form)


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    db = get_db()
    cur = db.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (id, current_user.id)
    )
    expense = cur.fetchone()
    if expense is None:
        abort(404)

    row = dict(expense)
    row["date"] = datetime.strptime(row["date"], "%Y-%m-%d").date()
    form = ExpenseForm(data=row)

    if form.validate_on_submit():
        try:
            db_update_expense(
                expense["id"],
                current_user.id,
                float(form.amount.data),
                form.category.data,
                form.date.data.isoformat(),
                form.description.data
            )
        except sqlite3.Error:
            app.logger.exception("edit_expense: database update failed")
            flash("Could not save the changes. Please try again.", "error")
            return render_template("edit_expense.html", form=form, expense_id=expense["id"])

        flash("Expense updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("edit_expense.html", form=form, expense_id=expense["id"])


@app.route("/expenses/<int:id>/delete", methods=["POST"])
@login_required
def delete_expense(id):
    db = get_db()
    row = db.execute(
        "SELECT id FROM expenses WHERE id = ? AND user_id = ?",
        (id, current_user.id)
    ).fetchone()
    db.close()

    if row is None:
        abort(404)

    try:
        db_delete_expense(id, current_user.id)
    except sqlite3.Error:
        app.logger.exception("Failed to delete expense id=%s user=%s", id, current_user.id)
        flash("Could not delete the expense. Please try again.", "error")
        return redirect(url_for("profile"))

    app.logger.info("Deleted expense id=%s user=%s", id, current_user.id)
    flash("Expense deleted.", "success")
    return redirect(url_for("profile"))


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
