# Spec: Edit Expense

## Overview
Allow logged-in users to edit expenses they previously recorded. Once a user has built up a transaction history, real spending data needs to be correctable — typos in amounts, wrong date, miscategorised items. This step finishes wiring the full CRUD path started by Step 7 (Add) and gives the profile page an Edit affordance so transactions can be revised without touching the database directly. Step 9 will add Delete; this step is just the update path.

## Depends on
- 01-database-setup (the `expenses` table with `id`, `user_id`, `amount`, `category`, `date`, `description` must exist)
- 02-registration (users must exist)
- 03-login-and-logout (session must be set; route must be `@login_required`)
- 05-profile-page-backend (expenses must be queryable per user)
- 07-add-expense (the `ExpenseForm` and form patterns to reuse)

## Routes
- `GET /expenses/<int:id>/edit` — render the edit form pre-filled with the existing expense — logged-in only
- `POST /expenses/<int:id>/edit` — validate and persist the updated expense — logged-in only

Both routes must reject (404 / redirect) any expense whose `user_id` does not match `current_user.id`.

## Database changes
No database changes. The existing `expenses` table is sufficient. Add an `update_expense` helper to `database/db.py` mirroring the `add_expense` helper:

```python
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
```

## Templates
- **Create:** `templates/edit_expense.html` — same structure as `add_expense.html` but:
  - Page title is "Edit Expense"
  - Submit button label is "Save changes"
  - A "Cancel" link returns to `/profile`
  - An "Delete this expense" link or button is NOT included (Step 9 owns delete)
- **Modify:** `templates/base.html` — no changes
- **Modify:** `templates/profile.html` — in each row of the transactions table, add an "Edit" link beside the amount that points to `url_for('edit_expense', id=transaction.id)`. The transaction dict must therefore include the row `id` (currently only `date, description, category, amount` are passed — extend the SELECT).

## Files to change
- `app.py` — replace the `/expenses/<int:id>/edit` stub with a real view function (`GET` and `POST`) that:
  - Looks up the expense by `id` joined against `current_user.id`
  - Returns 404 (via `abort(404)`) if no matching row exists — never reveal whether the id was wrong vs. owned by another user
  - On `GET`: pre-populates `ExpenseForm` with the existing values (`form.amount.data`, `form.category.data`, `form.date.data`, `form.description.data`)
  - On `POST` + `form.validate_on_submit()`: calls `db_update_expense(...)`, flashes success, redirects to `/profile`
  - On `POST` + validation failure: re-renders the form with errors (no DB write)
  - On DB error: flash a generic error and re-render the form
- `database/db.py` — add `update_expense` helper (shown above) and import it from `app.py`

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — every SQL string uses `?` placeholders, never f-strings for values
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Reuse `ExpenseForm` from Step 7 — do not duplicate field definitions in a new form class
- Owner check is mandatory: every query that touches an expense must include `AND user_id = ?` with `current_user.id`. Treat missing ownership as 404, never 403, never 200-with-empty-body (no information leak)
- The form's existing `validate_date` (no future dates) must continue to apply
- On successful update, redirect to `/profile` with a flash message — same feedback pattern as Step 7

## Definition of done
- [ ] `GET /expenses/<id>/edit` while logged in returns 200 and renders the expense's current values in the form
- [ ] `POST /expenses/<id>/edit` with valid data updates the row in the `expenses` table and redirects to `/profile` with a success flash
- [ ] `POST /expenses/<id>/edit` with invalid data (missing amount, future date, etc.) re-renders the form with errors and does not modify the row
- [ ] `GET /expenses/<id>/edit` for an expense that does not belong to the logged-in user returns 404
- [ ] `GET /expenses/<id>/edit` for a non-existent expense id returns 404
- [ ] `GET /expenses/<id>/edit` while logged out redirects to `/login`
- [ ] The profile page shows an "Edit" link next to each transaction that navigates to the edit form for that expense
- [ ] After editing, the next visit to `/profile` reflects the updated values (amount, category, date, description) without a hard refresh issue
- [ ] All SQL in the implementation uses `?` placeholders — no f-string or `.format()` interpolation of user values
- [ ] `templates/edit_expense.html` extends `base.html` and contains no hardcoded hex colour values
