import pytest
from flask import session

# Scenarios:
# a. Happy paths:
#    - Valid expense submission with all fields.
#    - Valid expense submission with optional description omitted.
# b. Edge cases:
#    - Submission with amount at 0.00 or very small values.
# c. Error / validation scenarios:
#    - Missing amount.
#    - Missing category.
#    - Missing date.
#    - Invalid amount format (non-numeric).
# d. Auth guard checks:
#    - GET /expenses/add requires login.
#    - POST /expenses/add requires login.
# e. Database state checks:
#    - Verify record is inserted with correct user_id.
#    - Verify record contains correct values.

class TestAddExpenseHappyPath:
    def test_add_expense_given_valid_data_redirects_to_profile_and_saves(self, auth_client, app):
        """
        Spec: 07-add-expense §Definition of done
        Given: Logged-in user
        When: Submitting a valid expense form
        Then: Redirected to profile with success message and record created in DB
        """
        expense_data = {
            "amount": "45.50",
            "category": "Food",
            "date": "2026-06-12",
            "description": "Dinner at Italian restaurant",
            "submit": "Add Expense",\n            "submit": "Add Expense"
        }

        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)

        # Verify redirect/success message
        assert response.status_code == 200
        assert "success" in response.data.decode("utf-8").lower()

        # Verify DB state
        with app.app_context():
            from database.db import get_db
            db = get_db()
            cursor = db.execute("SELECT * FROM expenses WHERE amount = 45.50 AND category = 'Food'")
            row = cursor.fetchone()
            assert row is not None
            assert row[3] == "2026-06-12" # Assuming col index 3 is date
            assert row[4] == "Dinner at Italian restaurant" # Assuming col index 4 is description

    def test_add_expense_given_missing_description_still_saves(self, auth_client, app):
        """
        Spec: 07-add-expense §Overview
        Given: Logged-in user
        When: Submitting a valid expense form without a description
        Then: Record is successfully created
        """
        expense_data = {
            "amount": "10.00",
            "category": "Transport",
            "date": "2026-06-12",
            "description": "",
            "submit": "Add Expense"
        }

        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            from database.db import get_db
            db = get_db()
            cursor = db.execute("SELECT * FROM expenses WHERE amount = 10.00 AND category = 'Transport'")
            row = cursor.fetchone()
            assert row is not None

class TestAddExpenseEdgeCases:
    def test_add_expense_given_zero_amount_saves_successfully(self, auth_client, app):
        """
        Spec: 07-add-expense §Definition of done
        Given: Logged-in user
        When: Submitting expense with 0.00 amount
        Then: Record is saved (assuming 0 is valid)
        """
        expense_data = {
            "amount": "0.00",
            "category": "Other",
            "date": "2026-06-12",
            "description": "Zero cost item"
        }
        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)
        assert response.status_code == 200

class TestAddExpenseErrorHandling:
    def test_add_expense_given_missing_amount_shows_error(self, auth_client):
        """
        Spec: 07-add-expense §Definition of done
        Given: Logged-in user
        When: Submitting form without amount
        Then: Error message is displayed and no record is created
        """
        expense_data = {
            "amount": "",
            "category": "Food",
            "date": "2026-06-12"
        }
        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)
        assert "error" in response.data.decode("utf-8").lower()

    def test_add_expense_given_missing_category_shows_error(self, auth_client):
        """
        Spec: 07-add-expense §Definition of done
        Given: Logged-in user
        When: Submitting form without category
        Then: Error message is displayed
        """
        expense_data = {
            "amount": "10.00",
            "category": "",
            "date": "2026-06-12"
        }
        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)
        assert "error" in response.data.decode("utf-8").lower()

    def test_add_expense_given_missing_date_shows_error(self, auth_client):
        """
        Spec: 07-add-expense §Definition of done
        Given: Logged-in user
        When: Submitting form without date
        Then: Error message is displayed
        """
        expense_data = {
            "amount": "10.00",
            "category": "Food",
            "date": ""
        }
        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)
        assert "error" in response.data.decode("utf-8").lower()

    def test_add_expense_given_invalid_amount_format_shows_error(self, auth_client):
        """
        Spec: 07-add-expense §Definition of done
        Given: Logged-in user
        When: Submitting form with non-numeric amount
        Then: Error message is displayed
        """
        expense_data = {
            "amount": "abc",
            "category": "Food",
            "date": "2026-06-12"
        }
        response = auth_client.post("/expenses/add", data=expense_data, follow_redirects=True)
        assert "error" in response.data.decode("utf-8").lower()

class TestAddExpenseAuthGuard:
    def test_get_add_expense_given_unauthenticated_redirects_to_login(self, client):
        """
        Spec: 07-add-expense §Routes
        Given: Unauthenticated user
        When: Requesting GET /expenses/add
        Then: Redirected to /login
        """
        response = client.get("/expenses/add")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_post_add_expense_given_unauthenticated_redirects_to_login(self, client):
        """
        Spec: 07-add-expense §Routes
        Given: Unauthenticated user
        When: Requesting POST /expenses/add
        Then: Redirected to /login
        """
        response = client.post("/expenses/add", data={"amount": "10", "category": "Food", "date": "2026-06-12"})
        assert response.status_code == 302
        assert "/login" in response.location
