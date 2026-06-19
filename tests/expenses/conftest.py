import pytest

@pytest.fixture
def app():
    """Isolated test DB app — never touches spendly.db."""
    from app import app as flask_app
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "DATABASE": "test_expenses.db",
        "SECRET_KEY": "test-secret-key"
    })
    with flask_app.app_context():
        from database.db import init_db, seed_db
        init_db()
        seed_db()
        yield flask_app
    # Cleanup test DB
    import os
    try:
        os.remove("test_expenses.db")
    except OSError:
        pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Test client pre-logged-in as the demo seed user."""
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    }, follow_redirects=False)
    # Verify login succeeded
    assert response.status_code == 302, f"Login failed: {response.data}"
    return client
