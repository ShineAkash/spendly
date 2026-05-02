---
# Spec: Date Filter for Profile Page

## Overview
Allow users to filter their expenses on the profile page by date range. This enhances the profile page from a simple "last 10 transactions" view to a useful tool for reviewing spending over specific periods (e.g., this month, last 30 days, or a custom range).

## Depends on
- 04-profile-page
- 05-profile-page-backend

## Routes
No new routes. The `/profile` route will be modified to handle optional date filter parameters.

## Database changes
No database changes.

## Templates
- **Modify:** `templates/profile.html` — Add a filter form (date inputs) and display the currently active filter.

## Files to change
- `app.py` — Update the `profile` route to accept `start_date` and `end_date` query parameters and adjust the SQL queries for transactions and stats.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate that `start_date` and `end_date` are valid date strings before using them in queries.
- If no dates are provided, default to the behavior of showing the most recent transactions (though the stats should ideally reflect all time or a sensible default if not filtered).

## Definition of done
- [ ] Profile page loads normally without any filters.
- [ ] Users can specify a start date and end date, and the transaction list updates to show only expenses within that range.
- [ ] The total spent and transaction count stats update to reflect the filtered range.
- [ ] The category breakdown updates to reflect the filtered range.
- [ ] Invalid date inputs are handled gracefully without crashing the app.
---
