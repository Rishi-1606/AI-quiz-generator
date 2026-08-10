"""
Shared pytest fixtures for all backend tests.

Provides:
  - test_db   : a fresh SQLAlchemy session backed by an in-memory SQLite DB,
                 reset between every test.
  - client    : FastAPI TestClient with get_db overridden to use test_db.
  - auth_headers : signs up a fresh user and returns Bearer token headers.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use an in-memory SQLite DB for tests (isolated, no disk file)
TEST_DB_URL = "sqlite:///:memory:"

# check_same_thread=False required for SQLite with multiple test threads
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def test_db():
    """
    Create all tables in the in-memory DB before each test,
    yield a session, then drop all tables after the test.
    This guarantees a completely clean slate per test.
    """
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(test_db):
    """
    FastAPI TestClient with the get_db dependency overridden so every
    request uses the same in-memory test database session.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # session lifecycle managed by test_db fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """
    Register a fresh test user and return the Authorization header dict.
    Uses a unique email so this fixture can be called multiple times
    within the same session without conflicts.
    """
    resp = client.post(
        "/api/auth/signup",
        json={
            "name":     "Test User",
            "email":    "testuser@example.com",
            "password": "testpassword123",
            "role":     "student",
        },
    )
    assert resp.status_code == 201, f"Signup failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers_b(client):
    """
    A second test user — used in ownership/isolation tests.
    """
    resp = client.post(
        "/api/auth/signup",
        json={
            "name":     "Other User",
            "email":    "otheruser@example.com",
            "password": "otherpassword123",
            "role":     "student",
        },
    )
    assert resp.status_code == 201, f"Signup B failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
