"""Tests for the User table and its endpoints (routers/auth.py, routers/users.py).

Uses the shared fixtures from conftest.py: `client`, `db_session`, `make_user`,
and `unique_suffix`. Registration is exercised directly only for the
registration-specific tests (1-3); everything else goes through `make_user`.
"""

from models import User
from conftest import unique_suffix


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_register_success_persists_user_and_hides_password(client, db_session):
    suffix = unique_suffix()
    username = f"reguser_{suffix}"
    email = f"{username}@example.test"
    password = "hunter2-testpass"

    r = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )

    assert r.status_code == 201
    body = r.json()

    assert body["username"] == username
    assert body["email"] == email
    assert "password" not in body
    assert "password_hash" not in body

    row = db_session.get(User, body["id"])
    assert row is not None
    assert row.username == username
    assert row.email == email
    assert row.password_hash != password
    assert row.password_hash  # actually hashed, non-empty

    # cleanup (this test bypasses make_user's auto-cleanup)
    db_session.query(User).filter(User.id == body["id"]).delete()
    db_session.commit()


def test_register_duplicate_email_returns_400(client, db_session, make_user):
    existing = make_user()
    suffix = unique_suffix()

    r = client.post(
        "/auth/register",
        json={
            "username": f"otheruser_{suffix}",
            "email": existing["email"],
            "password": "another-password",
        },
    )

    assert r.status_code == 400


def test_register_duplicate_username_returns_400(client, db_session, make_user):
    existing = make_user()
    suffix = unique_suffix()

    r = client.post(
        "/auth/register",
        json={
            "username": existing["username"],
            "email": f"different_{suffix}@example.test",
            "password": "another-password",
        },
    )

    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_success_returns_usable_token(client, make_user):
    user = make_user()

    r = client.post(
        "/auth/login",
        data={"username": user["username"], "password": user["password"]},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"

    # token should actually work against a protected endpoint
    r2 = client.get(
        f"/user/{user['id']}",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert r2.status_code == 200


def test_login_wrong_password_returns_401(client, make_user):
    user = make_user()

    r = client.post(
        "/auth/login",
        data={"username": user["username"], "password": "wrong-password"},
    )

    assert r.status_code == 401


def test_login_nonexistent_username_returns_401(client):
    r = client.post(
        "/auth/login",
        data={"username": f"no_such_user_{unique_suffix()}", "password": "whatever"},
    )

    assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /user/{user_id}
# ---------------------------------------------------------------------------


def test_get_user_without_auth_header_returns_401(client, make_user):
    user = make_user()

    r = client.get(f"/user/{user['id']}")

    assert r.status_code == 401


def test_get_own_user_returns_correct_fields_without_password(client, make_user):
    user = make_user()

    r = client.get(f"/user/{user['id']}", headers=user["headers"])

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == user["id"]
    assert body["username"] == user["username"]
    assert body["email"] == user["email"]
    assert "password" not in body
    assert "password_hash" not in body


def test_get_other_users_id_returns_404_not_403(client, make_user):
    user_a = make_user()
    user_b = make_user()

    r = client.get(f"/user/{user_b['id']}", headers=user_a["headers"])

    assert r.status_code == 404


def test_get_nonexistent_user_id_returns_404_same_shape_as_other_user(client, make_user):
    user = make_user()

    r_missing = client.get("/user/999999999", headers=user["headers"])
    assert r_missing.status_code == 404

    other = make_user()
    r_other = client.get(f"/user/{other['id']}", headers=user["headers"])
    assert r_other.status_code == 404

    # existence of the id shouldn't be distinguishable from the response body
    assert r_missing.json() == r_other.json()
