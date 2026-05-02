import pytest
from app import app as flask_app
from database.db import init_db, seed_db

@pytest.fixture
def app():
    """Isolated in-memory SQLite app — never touches spendly.db."""
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "DATABASE": ":memory:",
        "SECRET_KEY": "test-secret-key"
    })
    with flask_app.app_context():
        init_db()
        seed_db()
        yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Test client pre-logged-in as the demo seed user."""
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    }, follow_redirects=True)
    return client
