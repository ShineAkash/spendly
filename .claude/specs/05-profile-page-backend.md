# Spec: Profile Page Backend

## Overview
This feature replaces the hardcoded data in the `/profile` route with real database queries. The profile page will display actual user information, real expense transactions, accurate spending statistics, and genuine category breakdowns fetched from the existing `users` and `expenses` tables.

## Depends on
- Step 1: Database setup (schema must exist with `users` and `expenses` tables)
- Step 2: Registration (users must be creatable)
- Step 3: Login + Logout (session must be set)
- Step 4: Profile Page (UI template must exist)

## Routes
No new routes. This step modifies the existing `GET /profile` route to serve real data instead of hardcoded values.

## Database changes
No database changes. The existing `users` and `expenses` tables are sufficient.

## Templates
No new templates. The existing `templates/profile.html` is reused without modification.

## Files to change
- `app.py` — replace the hardcoded context in the `/profile` view function with real database queries:
  - Fetch the authenticated user's `name`, `email`, and `created_at` from `users` table
  - Query the `expenses` table for the user's transactions, ordered by date descending, limited to 10 most recent
  - Calculate `total_spent` as the sum of all the user's expenses
  - Calculate `transaction_count` as the count of all the user's expenses
  - Calculate `top_category` as the category with the highest sum of expenses
  - Calculate per-category totals and percentages from the `expenses` table

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — never string-format SQL
- All database queries must be parameterised with `?` placeholders
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `current_user.id` (from flask-login) to scope all expense queries to the logged-in user
- Member since date must come from `users.created_at`, formatted as "Month YYYY"
- Transactions must be ordered by date descending, limited to 10 results
- If a user has no expenses, display empty state (zero values, empty transaction list)
- All monetary values must be formatted to 2 decimal places in the template

## Definition of done
- [ ] Visiting `/profile` while logged in shows the authenticated user's real name and email
- [ ] Visiting `/profile` shows a real `created_at` date formatted as "Month YYYY"
- [ ] Visiting `/profile` shows the actual total spent sum from the expenses table
- [ ] Visiting `/profile` shows the actual transaction count from the expenses table
- [ ] Visiting `/profile` shows the actual top spending category
- [ ] The transaction table shows real expenses from the database (max 10, ordered by date desc)
- [ ] The category breakdown shows real per-category totals and percentages
- [ ] A user with no expenses sees zero values and an empty transaction table
- [ ] All SQL queries use parameterised `?` placeholders
