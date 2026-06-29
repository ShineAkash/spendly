import sqlite3
from datetime import date
from werkzeug.security import generate_password_hash
from flask import current_app

def get_db():
    # Fall back to the default DB path if called outside an app context
    # (e.g. from the `if __name__ == "__main__"` block in app.py).
    try:
        database = current_app.config.get("DATABASE", "spendly.db")
    except RuntimeError:
        database = "spendly.db"

    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
    finally:
        conn.close()

def seed_db():
    conn = get_db()
    try:
        cur = conn.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] > 0:
            return

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123"))
        )
        user_id = cur.lastrowid

        today = date.today()
        year = today.year
        month = today.month

        expenses = [
            (user_id, 12.50, "Food", f"{year}-{month:02d}-03", "Lunch at cafe"),
            (user_id, 45.00, "Transport", f"{year}-{month:02d}-07", "Uber ride"),
            (user_id, 120.00, "Bills", f"{year}-{month:02d}-10", "Monthly electricity"),
            (user_id, 30.00, "Health", f"{year}-{month:02d}-12", "Pharmacy"),
            (user_id, 25.00, "Entertainment", f"{year}-{month:02d}-15", "Movie tickets"),
            (user_id, 89.99, "Shopping", f"{year}-{month:02d}-18", "New shoes"),
            (user_id, 15.00, "Other", f"{year}-{month:02d}-21", "Parking fee"),
            (user_id, 55.00, "Food", f"{year}-{month:02d}-25", "Grocery run"),
        ]

        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )
        conn.commit()
    finally:
        conn.close()

def add_expense(user_id, amount, category, date, description):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description)
        )
        conn.commit()
    finally:
        conn.close()


def update_expense(expense_id, user_id, amount, category, date, description):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? "
            "WHERE id = ? AND user_id = ?",
            (amount, category, date, description, expense_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_expense(expense_id, user_id):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()
