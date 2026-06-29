# Spec: Delete Expense

## Overview
Allow logged-in users to permanently delete an expense they previously recorded. This finishes the full CRUD path started by Step 7 (Add) and Step 8 (Edit). Users must be able to remove transactions entered by mistake or no longer relevant so their transaction history stays accurate. The route is already stubbed at `GET /expenses/<int:id>/delete` in `app.py` returning a placeholder string; this step replaces that stub with a real deletion handler and surfaces a Delete affordance on the profile page and the edit form.

## Depends on
- 01-database-setup (the `expenses` table with `id` and `user_id` must exist)
- 02-registration (users must exist)
- 03-login-and-logout (session must be set; route must be `@login_required`)
- 05-profile-page-backend (expenses must be queryable per user)
- 07-add-expense (the `expenses` insert pattern and `current_user.id`-scoped queries)
- 08-edit-expense (the ownership-check + 404 pattern this step mirrors)

## Routes
- `POST /expenses/<int:id>/delete` — verify ownership, then permanently delete the expense row and redirect to `/profile` — logged-in only

A GET on the same path is intentionally **not** supported. Deletion must be a deliberate POST (with CSRF protection via Flask-WTF where applicable) so a stray link, prefetch, or crawler cannot wipe data. If a GET request hits the path, return 405 Method Not Allowed via `abort(405)` rather than re-rendering or redirecting.

## Database changes
No schema changes. The existing `expenses` table is sufficient. Add a `delete_expense` helper to `database/db.py` mirroring `update_expense` / `add_expense`:

```python
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
```

The `AND user_id = ?` clause is the ownership guard — the helper must never accept a raw `expense_id` without it.

## Templates
- **Create:** `templates/delete_expense.html` — a small confirmation page that:
  - Has page title "Delete expense"
  - Shows the expense being deleted as a read-only summary (date, category, amount, description) so the user can verify what they're about to remove
  - Contains a `POST` form with a "Delete" submit button (labelled "Delete expense")
  - Contains a "Cancel" link that returns to `/profile` without deleting
  - Contains no separate "Edit" link on this page (the Cancel path goes back to profile, where Edit still exists)
- **Modify:** `templates/profile.html` — in each row of the transactions table, add a "Delete" link beside the existing "Edit" link. The link must POST to `url_for('delete_expense', id=transaction.id)`. Use a small inline `<form method="post" action="{{ url_for('delete_expense', id=transaction.id) }}" style="display:inline">` wrapping a submit button styled as a link, OR a small JS handler — pick whichever matches the existing style of the profile page. The transaction dict already includes `id` (Step 8 added it), so no profile-route change is needed.
- **Modify:** `templates/edit_expense.html` — the previous spec said "Delete this expense is owned by Step 9". Add a "Delete this expense" link/button on the edit page that posts to `delete_expense`. The button must be visually distinct from "Save changes" so a user editing a row cannot accidentally delete it.
- **Modify:** `templates/base.html` — no changes (the nav already links to /expenses/add and /profile).

## Files to change
- `app.py` — replace the `GET /expenses/<int:id>/delete` stub with a real `POST /expenses/<int:id>/delete` view function that:
  - Looks up the expense by `id` joined against `current_user.id`
  - Returns `abort(404)` if no matching row exists — never reveal whether the id was wrong vs. owned by another user
  - If a request arrives via GET (or any non-POST method), returns `abort(405)` so accidental GETs from refreshes / crawlers cannot delete data
  - On valid POST: calls `db_delete_expense(expense_id, current_user.id)`, flashes a success message ("Expense deleted."), redirects to `/profile`
  - On DB error: flash a generic error ("Could not delete the expense. Please try again.") and redirect to `/profile` (no rollback, no half-delete)
  - Imports the new helper at the top: `from database.db import get_db, init_db, seed_db, add_expense as db_add_expense, update_expense as db_update_expense, delete_expense as db_delete_expense`
- `database/db.py` — add the `delete_expense` helper shown above
- `templates/profile.html` — add the Delete form/button per row next to the existing Edit link
- `templates/edit_expense.html` — add the "Delete this expense" button below the Save changes submit, posting to `delete_expense`
- `requirements.txt` — no changes expected (no new packages)

## Files to create
- `templates/delete_expense.html` — confirmation page rendered when a user clicks the Delete link from the profile page (uses a small GET-to-confirm pattern: the link points to `/expenses/<id>/delete`, the GET renders the confirmation template, and the form on that template POSTs to the same path)

Note: the "GET renders a confirmation page; POST actually deletes" pattern is the simplest fit for the existing stub (`GET /expenses/<int:id>/delete`) and keeps the affordance visible without needing JS. Adjust routes/titles accordingly if the implementation chooses a pure-POST path with no confirmation step instead.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — every SQL string uses `?` placeholders, never f-strings for values (this includes the `DELETE` query and any ownership-check `SELECT`)
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values; any new confirm/cancel buttons reuse the same `--danger` / `--accent` tokens already used elsewhere in the app
- All templates extend `base.html`
- Owner check is mandatory: every query that touches an expense must include `AND user_id = ?` with `current_user.id`. Treat missing ownership as 404, never 403, never 200-with-empty-body (no information leak)
- Deletion is permanent — no soft-delete, no `deleted_at` column. The `expenses` row is removed from the table; aggregates (`total_spent`, `transaction_count`, category breakdown) recompute on the next profile render
- After deletion, the user lands back on `/profile` so they immediately see the row gone and updated totals
- The Delete button must be visually distinct from Edit/Save so a misclick on the profile page cannot silently remove a row
- A GET request to the delete endpoint must NOT delete — return 405 if reached without a POST
- Logs every successful delete via `app.logger.info(...)` so the action is traceable; log DB failures via `app.logger.exception(...)`

## Definition of done
- [ ] `POST /expenses/<id>/delete` while logged in with an expense the user owns deletes the row from `expenses` and redirects to `/profile` with a success flash
- [ ] `POST /expenses/<id>/delete` while logged in with an expense owned by another user returns 404 and does NOT delete the row
- [ ] `POST /expenses/<id>/delete` with a non-existent expense id returns 404
- [ ] `POST /expenses/<id>/delete` while logged out redirects to `/login` (Flask-Login default), no delete occurs
- [ ] `GET /expenses/<id>/delete` does NOT delete — either renders the confirmation template (if a confirmation step is implemented) or returns 405
- [ ] After deletion, `/profile` no longer lists the row in the transactions table
- [ ] After deletion, `/profile` correctly recomputes `total_spent`, `transaction_count`, and category breakdown reflecting the removed row
- [ ] The profile page shows a "Delete" control next to each transaction that posts to `/expenses/<id>/delete`
- [ ] The edit page shows a "Delete this expense" control that posts to `/expenses/<id>/delete`
- [ ] All SQL in the implementation uses `?` placeholders — no f-string or `.format()` interpolation of user values
- [ ] `templates/delete_expense.html` extends `base.html` and contains no hardcoded hex colour values
- [ ] The `database.delete_expense` helper exists with the `AND user_id = ?` guard and is imported into `app.py`
- [ ] Manual DB inspection after a delete confirms the row is physically gone (no `deleted_at`, no soft state)
