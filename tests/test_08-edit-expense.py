"""
Tests for Step 08 — Edit Expense feature.

Spec: .claude/specs/08-edit-expense.md

Scenarios covered:
- Auth guards: GET/POST while logged out → redirect to /login
- Ownership / 404: another user's expense → 404 (not 403, not silent 200)
- GET prefills the form with current values
- POST happy path: updates the row, redirects to /profile, profile reflects new values
- POST validation errors: empty amount, future date, missing fields → re-render with errors, DB unchanged
- DB side effects: only the targeted row is touched, others unchanged
- Owner-scoped UPDATE helper: wrong user_id does not modify the row
"""

import pytest
from datetime import date, timedelta


# ---------------------------------------------------------------------- #
# Helpers                                                                 #
# ---------------------------------------------------------------------- #

def _seed_second_user_with_expense(app):
    """Create a second user with one expense for cross-user tests."""
    from werkzeug.security import generate_password_hash
    with app.app_context():
        from database.db import get_db
        db = get_db()
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Other User", "other@example.com", generate_password_hash("otherpass1"))
        )
        other_id = cur.lastrowid
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (other_id, 99.99, "Shopping", "2026-05-15", "Other user's purchase")
        )
        other_expense_id = cur.lastrowid
        db.commit()
    return other_id, other_expense_id


def _demo_expense_id(app):
    """Return the id of the demo user's first expense (id=1 after seed)."""
    with app.app_context():
        from database.db import get_db
        db = get_db()
        cur = db.execute("SELECT id FROM expenses WHERE user_id=1 ORDER BY id LIMIT 1")
        row = cur.fetchone()
        return row["id"]


def _fetch_expense(expense_id):
    from database.db import get_db
    db = get_db()
    cur = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    return cur.fetchone()


# ---------------------------------------------------------------------- #
# Auth guards                                                             #
# ---------------------------------------------------------------------- #

class TestEditExpenseAuthGuard:
    def test_get_edit_expense_given_unauthenticated_redirects_to_login(self, client):
        """
        Spec §Definition of done: GET /expenses/<id>/edit while logged out redirects to /login.
        """
        response = client.get("/expenses/1/edit")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_post_edit_expense_given_unauthenticated_redirects_to_login(self, client):
        """
        Spec §Routes: POST must be @login_required.
        """
        response = client.post(
            "/expenses/1/edit",
            data={"amount": "10.00", "category": "Food", "date": "2026-06-12"}
        )
        assert response.status_code == 302
        assert "/login" in response.location


# ---------------------------------------------------------------------- #
# GET prefills the form                                                   #
# ---------------------------------------------------------------------- #

class TestEditExpenseGetPrefill:
    def test_get_edit_expense_returns_200_and_renders_form(self, auth_client):
        """
        Spec §Routes (GET): renders the edit form pre-filled with the existing expense.
        Spec §Definition of done: returns 200.
        """
        expense_id = _demo_expense_id(auth_client.application)
        response = auth_client.get(f"/expenses/{expense_id}/edit")
        assert response.status_code == 200

    def test_get_edit_expense_prefills_form_with_existing_values(self, auth_client, app):
        """
        Spec §app.py: On GET, pre-populates ExpenseForm with the existing values.
        """
        expense_id = _demo_expense_id(app)
        original = _fetch_expense(expense_id)
        response = auth_client.get(f"/expenses/{expense_id}/edit")
        body = response.data.decode("utf-8")
        # The form input for amount should carry the original value
        assert f'value="{original["amount"]}"' in body
        # The category option should be selected
        assert f'value="{original["category"]}"' in body
        # Date should be pre-filled
        assert original["date"] in body
        # Description should appear
        assert original["description"] in body


# ---------------------------------------------------------------------- #
# Ownership / 404                                                         #
# ---------------------------------------------------------------------- #

class TestEditExpenseOwnership:
    def test_get_edit_other_users_expense_returns_404(self, auth_client, app):
        """
        Spec §Routes: Both routes must reject (404 / redirect) any expense whose user_id
        does not match current_user.id. Never reveal whether the id was wrong vs.
        owned by another user → 404 (not 403, not 200).
        """
        _, other_expense_id = _seed_second_user_with_expense(app)
        response = auth_client.get(f"/expenses/{other_expense_id}/edit")
        assert response.status_code == 404

    def test_post_edit_other_users_expense_returns_404_and_db_unchanged(
        self, auth_client, app
    ):
        """
        Spec §app.py: owner check is mandatory; treat missing ownership as 404.
        DB side effect: another user's row must NOT be modified.
        """
        _, other_expense_id = _seed_second_user_with_expense(app)
        before = _fetch_expense(other_expense_id)

        response = auth_client.post(
            f"/expenses/{other_expense_id}/edit",
            data={
                "amount": "1.00",
                "category": "Food",
                "date": "2026-06-12",
                "description": "HACKED",
                "submit": "Save changes",
            },
        )
        assert response.status_code == 404

        after = _fetch_expense(other_expense_id)
        assert after["amount"] == before["amount"]
        assert after["category"] == before["category"]
        assert after["description"] == before["description"]

    def test_get_edit_nonexistent_expense_returns_404(self, auth_client):
        """
        Spec §Definition of done: GET /expenses/<id>/edit for a non-existent id returns 404.
        """
        response = auth_client.get("/expenses/999999/edit")
        assert response.status_code == 404


# ---------------------------------------------------------------------- #
# POST happy path                                                         #
# ---------------------------------------------------------------------- #

class TestEditExpensePostHappyPath:
    def test_post_edit_expense_given_valid_data_updates_row_and_redirects(
        self, auth_client, app
    ):
        """
        Spec §Definition of done: POST with valid data updates the row and redirects
        to /profile with a success flash.
        """
        expense_id = _demo_expense_id(app)

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data={
                "amount": "77.77",
                "category": "Transport",
                "date": "2026-06-08",
                "description": "Edited description",
                "submit": "Save changes",
            },
        )
        assert response.status_code == 302
        assert "/profile" in response.location

        row = _fetch_expense(expense_id)
        assert row["amount"] == 77.77
        assert row["category"] == "Transport"
        assert row["date"] == "2026-06-08"
        assert row["description"] == "Edited description"

    def test_post_edit_expense_followed_by_profile_shows_new_values(
        self, auth_client, app
    ):
        """
        Spec §Definition of done: After editing, the next visit to /profile reflects
        the updated values without a hard refresh issue.
        """
        expense_id = _demo_expense_id(app)
        auth_client.post(
            f"/expenses/{expense_id}/edit",
            data={
                "amount": "55.55",
                "category": "Health",
                "date": "2026-06-09",
                "description": "Updated via edit",
                "submit": "Save changes",
            },
        )
        profile = auth_client.get("/profile")
        body = profile.data.decode("utf-8")
        assert "55.55" in body
        assert "Updated via edit" in body

    def test_post_edit_expense_only_touches_targeted_row(self, auth_client, app):
        """
        DB side effect: only the targeted row is updated, other rows for the same user
        are unchanged.
        """
        expense_id = _demo_expense_id(app)
        # Capture a sibling row
        with app.app_context():
            from database.db import get_db
            db = get_db()
            sibling = db.execute(
                "SELECT * FROM expenses WHERE user_id=1 AND id != ? ORDER BY id LIMIT 1",
                (expense_id,),
            ).fetchone()
            sibling = dict(sibling)

        auth_client.post(
            f"/expenses/{expense_id}/edit",
            data={
                "amount": "12.34",
                "category": "Other",
                "date": "2026-06-10",
                "description": "Touch only this one",
                "submit": "Save changes",
            },
        )

        with app.app_context():
            from database.db import get_db
            db = get_db()
            sibling_after = dict(
                db.execute(
                    "SELECT * FROM expenses WHERE id = ?", (sibling["id"],)
                ).fetchone()
            )
        assert sibling_after == sibling


# ---------------------------------------------------------------------- #
# POST validation errors                                                  #
# ---------------------------------------------------------------------- #

class TestEditExpensePostValidationErrors:
    def test_post_edit_given_missing_amount_does_not_modify_db(self, auth_client, app):
        """
        Spec §Definition of done: invalid data re-renders form with errors and does not
        modify the row.
        """
        expense_id = _demo_expense_id(app)
        before = dict(_fetch_expense(expense_id))

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data={
                "amount": "",
                "category": "Food",
                "date": "2026-06-12",
                "submit": "Save changes",
            },
        )
        # Validation failure → re-render (200), not redirect (302)
        assert response.status_code == 200
        body = response.data.decode("utf-8").lower()
        assert "error" in body

        after = dict(_fetch_expense(expense_id))
        assert after == before

    def test_post_edit_given_future_date_does_not_modify_db(self, auth_client, app):
        """
        Spec §app.py: The form's existing validate_date (no future dates) must continue to apply.
        """
        expense_id = _demo_expense_id(app)
        before = dict(_fetch_expense(expense_id))
        future = (date.today() + timedelta(days=30)).isoformat()

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data={
                "amount": "10.00",
                "category": "Food",
                "date": future,
                "submit": "Save changes",
            },
        )
        assert response.status_code == 200
        after = dict(_fetch_expense(expense_id))
        assert after == before

    def test_post_edit_given_zero_amount_does_not_modify_db(self, auth_client, app):
        """
        Spec §app.py: Reuse ExpenseForm — NumberRange(min=0.01) must reject 0.
        """
        expense_id = _demo_expense_id(app)
        before = dict(_fetch_expense(expense_id))

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data={
                "amount": "0.00",
                "category": "Food",
                "date": "2026-06-12",
                "submit": "Save changes",
            },
        )
        assert response.status_code == 200
        after = dict(_fetch_expense(expense_id))
        assert after == before


# ---------------------------------------------------------------------- #
# Profile page integration                                                #
# ---------------------------------------------------------------------- #

class TestProfileEditLink:
    def test_profile_shows_edit_link_per_transaction(self, auth_client, app):
        """
        Spec §Definition of done: The profile page shows an "Edit" link next to each
        transaction that navigates to the edit form for that expense.
        """
        with app.app_context():
            from database.db import get_db
            db = get_db()
            count = db.execute(
                "SELECT COUNT(*) AS c FROM expenses WHERE user_id=1"
            ).fetchone()["c"]

        body = auth_client.get("/profile").data.decode("utf-8")
        # The transactions table is capped at 10 — assert ≤ min(count, 10)
        expected = min(count, 10)
        assert body.count("trans-edit-link") == expected
        # Each link must point to /expenses/<id>/edit
        assert body.count("/expenses/") >= expected


# ---------------------------------------------------------------------- #
# update_expense() helper — unit tests                                    #
# ---------------------------------------------------------------------- #

class TestUpdateExpenseHelper:
    def test_update_expense_with_correct_user_id_updates_row(self, app):
        """
        Spec §database changes: UPDATE only touches the row when user_id matches.
        """
        expense_id = _demo_expense_id(app)
        with app.app_context():
            from database.db import update_expense
            update_expense(expense_id, 1, 99.99, "Other", "2026-06-15", "Helper test")
            row = _fetch_expense(expense_id)
        assert row["amount"] == 99.99
        assert row["category"] == "Other"
        assert row["date"] == "2026-06-15"
        assert row["description"] == "Helper test"

    def test_update_expense_with_wrong_user_id_does_not_modify_row(self, app):
        """
        Spec §database changes: WHERE id = ? AND user_id = ? — mismatched user_id
        must not touch the row.
        """
        expense_id = _demo_expense_id(app)
        before = dict(_fetch_expense(expense_id))

        with app.app_context():
            from database.db import update_expense
            update_expense(expense_id, 999, 1.00, "Food", "2026-06-12", "Should not apply")

        after = dict(_fetch_expense(expense_id))
        assert after == before

    def test_update_expense_with_nonexistent_id_does_not_error(self, app):
        """
        Helper must be silent on missing rows (no exception); spec does not require
        raising — it only requires that nothing else gets touched.
        """
        with app.app_context():
            from database.db import update_expense
            update_expense(999999, 1, 1.00, "Food", "2026-06-12", "x")