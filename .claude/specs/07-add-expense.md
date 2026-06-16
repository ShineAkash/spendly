# Spec: Add Expense

## Overview
This feature allows logged-in users to record new expenses in their account. It provides a form to input the amount, category, date, and an optional description. This is a core part of the expense tracking functionality, enabling users to build their transaction history.

## Depends on
05-profile-page-backend

## Routes
- `GET /expenses/add` — Show the expense addition form — logged-in
- `POST /expenses/add` — Process the form and save the expense to the database — logged-in

## Database changes
No database changes.

## Templates
- **Create:** `templates/add_expense.html`
- **Modify:** `templates/base.html` (to add a link to the "Add Expense" page)

## Files to change
- `app.py`

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- A user can navigate to `/expenses/add`.
- The "Add Expense" form is displayed.
- Form validation ensures required fields (amount, category, date) are present.
- Submitting a valid form adds a new record to the `expenses` table for the currently logged-in user.
- After successful submission, the user is redirected to their profile page with a success message.
- Invalid submissions trigger an error message.
