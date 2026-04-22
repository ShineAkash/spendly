# Spec: Login and Logout

## Overview
User authentication for Spendly. Allows existing users to sign in with email and password, and sign out. This builds on the registration feature (Step 2) to complete the authentication layer of the Spendly roadmap.

## Depends on
- 01-database-setup (users table with password_hash field)
- 02-registration (existing user accounts)

## Routes

- `GET /login` — Show login form — public
- `POST /login` — Authenticate user, create session — public
- `POST /logout` — Clear session, sign out — logged-in

## Database changes

No new tables or columns. The `users` table from Step 1 is used as-is.

## Templates

### Create
- None

### Modify
- `templates/login.html` — Ensure form posts to POST /login, add flash message display

## Files to change
- `app.py` — Replace `/login` and `/logout` stubs with functional handlers:
  - Add `login_user()` and `logout_user()` functions using Flask session
  - Add `load_user()` helper to retrieve user from session
  - Add login required decorator
  - Implement POST /login with email/password validation
  - Implement /logout to clear session
- `templates/base.html` — Add dynamic nav links for logged-in vs logged-out state

## Files to create
- `app.py` — Add `login_required` decorator before routes that require authentication

## New dependencies
- `flask-login` — For session management (add to requirements.txt)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords verified with werkzeug (check_password_hash)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Store user_id in Flask session (not password hash)
- Use flask-login's session management pattern
- CSRF protection on all POST forms via Flask-WTF

## Definition of done
- [ ] GET /login renders the login form
- [ ] POST /login with valid email/password creates a session and redirects to profile
- [ ] POST /login with invalid credentials shows an error message
- [ ] POST /login with non-existent email shows an error message
- [ ] Clicking logout clears the session and redirects to /login
- [ ] Logged-in users see profile link in nav; logged-out users see sign in link
- [ ] Visiting /profile while logged-out redirects to /login
- [ ] Flash messages display on login page for error/success states
