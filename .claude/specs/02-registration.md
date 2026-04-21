# Spec: Registration

## Overview
User registration for Spendly. Allows new users to create an account with name, email, and password. This is the first authentication step in the Spendly roadmap — login (Step 3) follows immediately after.

## Depends on
- 01-database-setup (users table already exists with password_hash field)

## Routes

- `GET /register` — Show registration form — public
- `POST /register` — Process registration form — public

No new routes.

## Database changes

No new tables or columns. The `users` table from Step 1 is used as-is.

## Templates

### Create
- None (register.html already exists as a placeholder)

### Modify
- `templates/register.html` — Replace placeholder with full registration form:
  - Name input (required, min 2 chars)
  - Email input (required, valid email format)
  - Password input (required, min 8 chars)
  - Confirm password input (required, must match)
  - Submit button
  - Link to login page
  - Error message display area
  - CSRF protection via Flask-WTF or manual token

## Files to change
- `app.py` — Replace `/register` stub with functional POST handler
- `templates/register.html` — Full form implementation

## Files to create
- None

## New dependencies
- `flask-wtf` — For CSRF protection (add to requirements.txt)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (generate_password_hash)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate inputs server-side before inserting
- Check for duplicate email before creating user
- Store error messages in Flask flash system
- Redirect to login page on successful registration with a success flash message

## Definition of done
- [ ] GET /register renders the registration form
- [ ] POST /register with valid data creates a new user in the database
- [ ] Password is hashed before storage (not stored in plain text)
- [ ] POST /register with duplicate email shows an error message
- [ ] POST /register with missing/invalid fields shows field-specific errors
- [ ] Successful registration redirects to /login with a flash success message
- [ ] Registration form submits via POST (not GET)
- [ ] CSRF token is validated on form submission
