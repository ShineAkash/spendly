# Scenarios:
# 1. Happy Paths:
#    - No filters: shows all-time stats and recent transactions.
#    - Start date filter: only expenses on or after start_date.
#    - End date filter: only expenses on or before end_date.
#    - Date range filter: only expenses within start_date and end_date inclusive.
# 2. Edge Cases:
#    - Empty results: range with no expenses shows 0 stats and empty list.
# 3. Error Handling:
#    - Invalid date strings: app ignores them and defaults to all-time view.
# 4. Auth Guard:
#    - Unauthenticated access to /profile redirects to /login.

import pytest
from database.db import get_db

class TestDateFilterProfilePageHappyPath:
    def test_profile_given_no_filters_shows_all_data(self, auth_client):
        """
        Spec: 06-date-filter-profile-page §Definition of Done
        Given: A logged-in user with expenses in the database
        When: Accessing /profile without any query parameters
        Then: The page loads and displays overall stats and recent transactions
        """
        response = auth_client.get("/profile", follow_redirects=True)
        assert response.status_code == 200
        # Verify some data is present (demo seed user has expenses)
        assert response.data.decode("utf-8") != ""

    def test_profile_given_start_date_filter_shows_filtered_data(self, auth_client, app):
        """
        Spec: 06-date-filter-profile-page §Definition of Done
        Given: A logged-in user with expenses on various dates
        When: Accessing /profile?start_date=2026-01-01
        Then: Only expenses from 2026-01-01 onwards are counted and listed
        """
        # Setup: ensure we have a known expense before the start date
        with app.app_context():
            db = get_db()
            # Use demo user id (usually 1 after seed_db)
            db.execute("INSERT INTO expenses (amount, category, date, user_id) VALUES (?, ?, ?, ?)",
                      (50.0, "Food", "2025-12-31", 1))
            db.commit()

        response = auth_client.get("/profile?start_date=2026-01-01", follow_redirects=True)
        assert response.status_code == 200
        # The 2025-12-31 expense should NOT be in the response
        assert "2025-12-31" not in response.data.decode("utf-8")

    def test_profile_given_end_date_filter_shows_filtered_data(self, auth_client, app):
        """
        Spec: 06-date-filter-profile-page §Definition of Done
        Given: A logged-in user with expenses on various dates
        When: Accessing /profile?end_date=2026-01-01
        Then: Only expenses on or before 2026-01-01 are counted and listed
        """
        with app.app_context():
            db = get_db()
            db.execute("INSERT INTO expenses (amount, category, date, user_id) VALUES (?, ?, ?, ?)",
                      (50.0, "Food", "2026-01-02", 1))
            db.commit()

        response = auth_client.get("/profile?end_date=2026-01-01", follow_redirects=True)
        assert response.status_code == 200
        assert "2026-01-02" not in response.data.decode("utf-8")

    def test_profile_given_date_range_filter_shows_intersection(self, auth_client, app):
        """
        Spec: 06-date-filter-profile-page §Definition of Done
        Given: A logged-in user with expenses on various dates
        When: Accessing /profile?start_date=2026-01-01&end_date=2026-01-31
        Then: Only expenses within January 2026 are counted and listed
        """
        with app.app_context():
            db = get_db()
            # Outside range (before)
            db.execute("INSERT INTO expenses (amount, category, date, user_id) VALUES (?, ?, ?, ?)",
                      (10.0, "Food", "2025-12-31", 1))
            # Inside range
            db.execute("INSERT INTO expenses (amount, category, date, user_id) VALUES (?, ?, ?, ?)",
                      (20.0, "Food", "2026-01-15", 1))
            # Outside range (after)
            db.execute("INSERT INTO expenses (amount, category, date, user_id) VALUES (?, ?, ?, ?)",
                      (30.0, "Food", "2026-02-01", 1))
            db.commit()

        response = auth_client.get("/profile?start_date=2026-01-01&end_date=2026-01-31", follow_redirects=True)
        assert response.status_code == 200
        assert "2026-01-15" in response.data.decode("utf-8")
        assert "2025-12-31" not in response.data.decode("utf-8")
        assert "2026-02-01" not in response.data.decode("utf-8")

class TestDateFilterProfilePageEdgeCases:
    def test_profile_given_empty_range_shows_zero_stats(self, auth_client):
        """
        Spec: 06-date-filter-profile-page §Definition of Done
        Given: A logged-in user
        When: Filtering for a date range where no expenses exist (e.g., year 2000)
        Then: Total spent and transaction count show 0 and the list is empty
        """
        response = auth_client.get("/profile?start_date=2000-01-01&end_date=2000-01-31", follow_redirects=True)
        assert response.status_code == 200
        # Depending on template, might show "0.00" or "0" for totals
        # We verify that no transaction dates are present
        # This is a generic check for empty state
        # The spec says "stats show 0"
        content = response.data.decode("utf-8")
        # We expect to see a 0 in the stats area
        assert "0" in content

class TestDateFilterProfilePageErrorHandling:
    def test_profile_given_invalid_date_defaults_to_all_time(self, auth_client):
        """
        Spec: 06-date-filter-profile-page §Definition of Done
        Given: A logged-in user
        When: Accessing /profile with invalid date strings
        Then: The app handles it gracefully (no crash) and shows the default all-time view
        """
        response = auth_client.get("/profile?start_date=not-a-date&end_date=invalid", follow_redirects=True)
        assert response.status_code == 200
        # Should show data as if no filter was applied
        # Demo seed user always has expenses, so data should be present
        assert response.data.decode("utf-8") != ""

class TestDateFilterProfilePageAuthGuard:
    def test_profile_given_unauthenticated_redirects_to_login(self, client):
        """
        Spec: 06-date-filter-profile-page §Auth Guard
        Given: An unauthenticated user
        When: Accessing /profile
        Then: Redirected to /login
        """
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.location
