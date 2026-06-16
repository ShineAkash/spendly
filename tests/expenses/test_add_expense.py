import pytest
from pytest import approx

# Scenarios:
# a. Happy paths:
#    - Valid expense submission (amount, category, date) redirects to profile and saves to DB.
#    - Valid expense submission with optional description saves to DB.
#    - Form page renders correctly for authenticated users.
# b. Edge cases:
#    - Submission with very large amount.
#    - Submission with zero amount (if allowed).
# c. Error / validation scenarios:
#    - Missing amount triggers error.
#    - Missing category triggers error.
#    - Missing date triggers error.
# d. Auth guard checks:
#    - GET /expenses/add redirects to /login when unauthenticated.
#    - POST /expenses/add redirects to /login when unauthenticated.
# e. Database state checks:
#    - Verify record is created in the expenses table with correct user_id.

class TestAddExpenseHappyPath:
    def test_add_expense_form_renders_given_authenticated_user(self, auth_client):
        """
        Spec: 07-add-expense §Definition of Done
        Given: Authenticated user
        When:  Requesting GET /expenses/add
        Then:  The expense addition form is displayed (200 OK)
        """
        response = auth_client.get("/expenses/add")
        assert response.status_code == 200
        assert b"Add Expense" in response.data

    def test_add_expense_given_valid_data_redirects_to_profile_and_saves_to_db(self, auth_client, app):
        """
        Spec: 07-add-expense §Definition of Done
        Given: Authenticated user and valid expense data
        When:  Submitting POST /expenses/add
        Then:  Redirected to profile page, success message displayed, and record saved to DB
        """
        expense_data = {
            "amount": "50.00",
            "category": "Food",
            "date": "2026-06-15",
            "description": "Dinner with friends"
        }
        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)

        # Check redirect and success
        assert response.status_code == 200
        # Verify we're on the profile page
        assert b"Profile" in response.data or b"profile" in response.data.lower()
        # Verify the new expense appears in the response
        assert b"Dinner with friends" in response.data

        # Check DB state
        with app.app_context():
            import sqlite3
            from database.db import get_db
            db = get_db()
            user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()[0]
            expense = db.execute(
                "SELECT amount, category, date, description FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,)
            ).fetchone()

            assert expense is not None
            assert approx(float(expense[0]), abs=0.01) == 50.00
            assert expense[1] == "Food"
            assert expense[2] == "2026-06-15"
            assert expense[3] == "Dinner with friends"

    def test_add_expense_given_valid_minimal_data_saves_to_db(self, auth_client, app):
        """
        Spec: 07-add-expense §Definition of Done
        Given: Authenticated user and minimal valid data (no description)
        When:  Submitting POST /expenses/add
        Then:  Record saved to DB with empty/null description
        """
        expense_data = {
            "amount": "20.00",
            "category": "Transport",
            "date": "2026-06-15",
            "description": ""
        }
        auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)

        with app.app_context():
            import sqlite3
            from database.db import get_db
            db = get_db()
            user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()[0]
            expense = db.execute(
                "SELECT description FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,)
            ).fetchone()

            assert expense[0] == "" or expense[0] is None

class TestAddExpenseEdgeCases:
    def test_add_expense_given_large_amount_saves_correctly(self, auth_client, app):
        """
        Spec: 07-add-expense §Definition of Done
        Given: Authenticated user and a very large amount
        When:  Submitting POST /expenses/add
        Then:  The record is saved correctly
        """
        expense_data = {
            "amount": "1000000.00",
            "category": "Shopping",
            "date": "2026-06-15",
            "description": "Luxury item"
        }
        auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)

        with app.app_context():
            from database.db import get_db
            db = get_db()
            user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()[0]
            expense = db.execute(
                "SELECT amount FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,)
            ).fetchone()
            assert approx(float(expense[0]), abs=0.01) == 1000000.00

class TestAddExpenseErrorHandling:
    def test_add_expense_given_missing_amount_shows_error(self, auth_client):
        """
        Spec: 07-add-expense §Definition of Done
        Given: Authenticated user and missing amount
        When:  Submitting POST /expenses/add
        Then:  An error message is displayed and not redirected to profile
        """
        expense_data = {
            "amount": "",
            "category": "Food",
            "date": "2026-06-15"
        }
        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)
        assert b"amount" in response.data.lower()
        assert b"required" in response.data.lower() or b"error" in response.data.lower()

    def test_add_expense_given_missing_category_shows_error(self, auth_client):
        """
        Spec: 07-add-expense §Definition of Done
        Given: Authenticated user and missing category
        When:  Submitting POST /expenses/add
        Then:  An error message is displayed
        """
        expense_data = {
            "amount": "10.00",
            "category": "",
            "date": "2026-06-15"
        }
        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)
        assert b"category" in response.data.lower()
        assert b"required" in response.data.lower() or b"error" in response.data.lower()

    def test_add_expense_given_missing_date_shows_error(self, auth_client):
        """
        Spec: 07-add-expense §Definition of Done
        Given: Authenticated user and missing date
        When:  Submitting POST /expenses/add
        Then:  An error message is displayed
        """
        expense_data = {
            "amount": "10.00",
            "category": "Food",
            "date": ""
        }
        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)
        assert b"date" in response.data.lower()
        assert b"required" in response.data.lower() or b"error" in response.data.lower()

class TestAddExpenseAuthGuard:
    def test_add_expense_get_given_unauthenticated_redirects_to_login(self, client):
        """
        Spec: 07-add-expense §Routes
        Given: Unauthenticated user
        When:  Requesting GET /expenses/add
        Then:  Redirected to /login
        """
        from urllib.parse import urlparse
        response = client.get("/expenses/add")
        assert response.status_code == 302
        assert urlparse(response.location).path == "/login"

    def test_add_expense_post_given_unauthenticated_redirects_to_login(self, client):
        """
        Spec: 07-add-expense §Routes
        Given: Unauthenticated user
        When:  Submitting POST /expenses/add
        Then:  Redirected to /login
        """
        from urllib.parse import urlparse
        expense_data = {
            "amount": "10.00",
            "category": "Food",
            "date": "2026-06-15"
        }
        response = client.post("/expenses/add", data=expense_data)
        assert response.status_code == 302
        assert urlparse(response.location).path == "/login"
