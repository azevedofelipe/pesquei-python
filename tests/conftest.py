"""Shared pytest fixtures for the whole test suite.

Tests run against a dedicated `pesquei_test` Postgres database (never the
real dev database) so they can assert real persistence — "does this row
actually show up in the database" — without touching real data. The
DATABASE_URL env var is redirected to pesquei_test *before* `database.py`/
`main.py` are imported anywhere, since `database.py` builds its engine from
the env var at import time.

Each test is responsible for cleaning up the rows it creates (there is no
transaction-rollback isolation here — requests go through the real app,
which calls `db.commit()` itself). Use the `make_user` fixture factory,
which registers its own cleanup, instead of hand-rolling registration.
"""

import os
import secrets
import uuid
from urllib.parse import urlsplit, urlunsplit

import pytest
from dotenv import load_dotenv

load_dotenv()

_real_url = os.environ["DATABASE_URL"]
_parts = urlsplit(_real_url)
TEST_DATABASE_URL = urlunsplit((_parts.scheme, _parts.netloc, "/pesquei_test", "", ""))
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from models import Base, Catch, Lure, User  # noqa: E402

_test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=_test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Idempotent: only creates tables that don't already exist. Safe to run
    from multiple pytest processes at once (e.g. several agents in parallel)
    since it makes no DDL calls once the schema already exists."""
    Base.metadata.create_all(_test_engine, checkfirst=True)
    yield


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    """A fresh session for direct verification queries — independent of
    whatever session the app used to handle the request, so a passing
    assertion here means the data is genuinely in the database, not just
    held in some in-memory object."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


def unique_suffix() -> str:
    """Collision-safe even across multiple pytest processes running at the
    same time (different agents testing different tables concurrently)."""
    return f"{os.getpid()}_{uuid.uuid4().hex[:10]}"


@pytest.fixture
def make_user(client, db_session):
    """Factory fixture: call make_user() (or make_user(username=...)) to
    register + log in a throwaway user via the real API. Returns a dict with
    id/username/email/password/headers. Cleans up everything it created
    (catches, then lures, then the user, in FK-safe order) after the test,
    regardless of what the test did with that user."""
    created_user_ids = []

    def _make_user(username: str | None = None, password: str = "hunter2-testpass"):
        suffix = unique_suffix()
        username = username or f"testuser_{suffix}"
        email = f"{username}@example.test"

        r = client.post(
            "/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        assert r.status_code == 201, f"register failed: {r.status_code} {r.text}"
        user = r.json()

        r = client.post("/auth/login", data={"username": username, "password": password})
        assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
        token = r.json()["access_token"]

        created_user_ids.append(user["id"])

        return {
            "id": user["id"],
            "username": username,
            "email": email,
            "password": password,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    yield _make_user

    for uid in created_user_ids:
        db_session.query(Catch).filter(Catch.user_id == uid).delete()
        db_session.query(Lure).filter(Lure.user_id == uid).delete()
        db_session.query(User).filter(User.id == uid).delete()
    db_session.commit()


def random_hex(n: int = 6) -> str:
    return secrets.token_hex(n)
