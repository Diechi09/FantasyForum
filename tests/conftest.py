import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import Post, User
from app.services.posts import ensure_flair_column

@pytest.fixture
def app():
    # Use in-memory DB and disable CSRF for tests
    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=False,
    )
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        ensure_flair_column()  # no-op if column exists
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user(app):
    u = User(username="alice", email="alice@example.com")
    u.set_password("password123")
    db.session.add(u)
    db.session.commit()
    return u

@pytest.fixture
def other_user(app):
    u = User(username="bob", email="bob@example.com")
    u.set_password("password123")
    db.session.add(u)
    db.session.commit()
    return u

@pytest.fixture
def login(client, user):
    """Log in as 'alice' and return the test client."""
    r = client.post("/login",
                    data={"email": "alice@example.com", "password": "password123"},
                    follow_redirects=True)
    assert r.status_code == 200
    return client

@pytest.fixture
def sample_post(app, user):
    p = Post(title="Hello", flair="OTHER", content="Test content", author=user)
    db.session.add(p)
    db.session.commit()
    return p
