"""Tests for the Catch table and its endpoints (routers/catches.py).

Uses the shared fixtures from conftest.py: `client`, `db_session`, and
`make_user`. Every catch needs an owning user, so `make_user()` is used for
every test - it also cleans up any catches (and lures) that user owns.

Note: `CatchCreate.date_caught` has a known, already-logged bug (see
AGENTS.md "CatchCreate.date_caught default is a bug") where its default is
evaluated once at import time, not per request. `date_caught` is always
passed explicitly below to avoid relying on that default.
"""

from datetime import datetime

import pytest

from models import Catch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _full_payload(**overrides):
    payload = {
        "date_caught": "2026-05-01T10:30:00",
        "species": "Largemouth Bass",
        "weight": 4.5,
        "length": 45.5,
        "latitude": -23.55052,
        "longitude": -46.633308,
        "lure_id": None,
        "depth": 12.5,
        "notes": "Caught near the dock at sunset",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# POST /catch/
# ---------------------------------------------------------------------------


def test_create_catch_full_fields_persists_correctly(client, db_session, make_user):
    user = make_user()
    payload = _full_payload()

    r = client.post("/catch/", json=payload, headers=user["headers"])

    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body["user_id"] == user["id"]
    assert "id" in body

    row = db_session.get(Catch, body["id"])
    assert row is not None
    assert row.user_id == user["id"]
    assert row.date_caught == datetime.fromisoformat(payload["date_caught"])
    assert row.species == payload["species"]
    assert float(row.weight) == pytest.approx(payload["weight"])
    assert float(row.length) == pytest.approx(payload["length"])
    assert float(row.latitude) == pytest.approx(payload["latitude"])
    assert float(row.longitude) == pytest.approx(payload["longitude"])
    assert row.lure_id is None
    assert float(row.depth) == pytest.approx(payload["depth"])
    assert row.notes == payload["notes"]


def test_create_catch_minimal_fields_only_date_caught(client, db_session, make_user):
    user = make_user()
    payload = {"date_caught": "2026-05-02T08:00:00"}

    r = client.post("/catch/", json=payload, headers=user["headers"])

    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body["user_id"] == user["id"]
    for field in ("species", "weight", "length", "latitude", "longitude", "lure_id", "depth", "notes"):
        assert body.get(field) is None

    row = db_session.get(Catch, body["id"])
    assert row is not None
    assert row.date_caught == datetime.fromisoformat(payload["date_caught"])
    assert row.species is None
    assert row.weight is None
    assert row.length is None
    assert row.latitude is None
    assert row.longitude is None
    assert row.lure_id is None
    assert row.depth is None
    assert row.notes is None


def test_create_catch_with_lure_id_persists_fk(client, db_session, make_user):
    user = make_user()

    r_lure = client.post(
        "/lure/",
        json={"name": "Silver Spoon", "type": "spoon"},
        headers=user["headers"],
    )
    assert r_lure.status_code in (200, 201), r_lure.text
    lure_id = r_lure.json()["id"]

    payload = _full_payload(lure_id=lure_id)
    r = client.post("/catch/", json=payload, headers=user["headers"])

    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body["user_id"] == user["id"]

    row = db_session.get(Catch, body["id"])
    assert row is not None
    assert row.lure_id == lure_id


def test_create_catch_without_auth_header_returns_401(client, make_user):
    payload = _full_payload()

    r = client.post("/catch/", json=payload)

    assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /catch/
# ---------------------------------------------------------------------------


def test_list_catches_returns_exactly_owners_catches(client, db_session, make_user):
    user = make_user()

    created_ids = []
    for i in range(3):
        r = client.post(
            "/catch/",
            json=_full_payload(date_caught=f"2026-05-0{i + 1}T09:00:00", species=f"Species {i}"),
            headers=user["headers"],
        )
        assert r.status_code in (200, 201), r.text
        created_ids.append(r.json()["id"])

    r = client.get("/catch/", headers=user["headers"])

    assert r.status_code == 200
    body = r.json()
    assert {c["id"] for c in body} == set(created_ids)
    assert all(c["user_id"] == user["id"] for c in body)


def test_list_catches_excludes_other_users_catches(client, db_session, make_user):
    user_a = make_user()
    user_b = make_user()

    for i in range(2):
        r = client.post(
            "/catch/",
            json=_full_payload(date_caught=f"2026-05-1{i}T09:00:00"),
            headers=user_a["headers"],
        )
        assert r.status_code in (200, 201), r.text

    r = client.post(
        "/catch/",
        json=_full_payload(date_caught="2026-05-20T09:00:00", species="Only Bs Catch"),
        headers=user_b["headers"],
    )
    assert r.status_code in (200, 201), r.text
    user_b_catch_id = r.json()["id"]

    r = client.get("/catch/", headers=user_b["headers"])

    assert r.status_code == 200
    body = r.json()
    assert {c["id"] for c in body} == {user_b_catch_id}
    assert all(c["user_id"] == user_b["id"] for c in body)


# ---------------------------------------------------------------------------
# GET /catch/{catch_id}
# ---------------------------------------------------------------------------


def test_get_own_catch_returns_correct_fields(client, make_user):
    user = make_user()
    payload = _full_payload()
    r_create = client.post("/catch/", json=payload, headers=user["headers"])
    assert r_create.status_code in (200, 201), r_create.text
    catch_id = r_create.json()["id"]

    r = client.get(f"/catch/{catch_id}", headers=user["headers"])

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == catch_id
    assert body["user_id"] == user["id"]
    assert body["species"] == payload["species"]
    assert body["notes"] == payload["notes"]
    assert body["date_caught"] == datetime.fromisoformat(payload["date_caught"]).isoformat()


def test_get_other_users_catch_returns_404(client, make_user):
    user_a = make_user()
    user_b = make_user()

    r_create = client.post("/catch/", json=_full_payload(), headers=user_a["headers"])
    assert r_create.status_code in (200, 201), r_create.text
    catch_id = r_create.json()["id"]

    r = client.get(f"/catch/{catch_id}", headers=user_b["headers"])

    assert r.status_code == 404


def test_get_nonexistent_catch_returns_404_same_shape_as_other_users_catch(client, make_user):
    user_a = make_user()
    user_b = make_user()

    r_create = client.post("/catch/", json=_full_payload(), headers=user_a["headers"])
    assert r_create.status_code in (200, 201), r_create.text
    other_users_catch_id = r_create.json()["id"]

    r_missing = client.get("/catch/999999999", headers=user_b["headers"])
    assert r_missing.status_code == 404

    r_other = client.get(f"/catch/{other_users_catch_id}", headers=user_b["headers"])
    assert r_other.status_code == 404

    assert r_missing.json() == r_other.json()


# ---------------------------------------------------------------------------
# PATCH /catch/{catch_id}
# ---------------------------------------------------------------------------


def test_patch_updates_only_targeted_field(client, db_session, make_user):
    user = make_user()
    payload = _full_payload()
    r_create = client.post("/catch/", json=payload, headers=user["headers"])
    assert r_create.status_code in (200, 201), r_create.text
    catch_id = r_create.json()["id"]

    r = client.patch(f"/catch/{catch_id}", json={"notes": "Updated notes"}, headers=user["headers"])

    assert r.status_code == 200
    body = r.json()
    assert body["notes"] == "Updated notes"
    assert body["species"] == payload["species"]

    row = db_session.get(Catch, catch_id)
    assert row.notes == "Updated notes"
    assert row.species == payload["species"]
    assert float(row.weight) == pytest.approx(payload["weight"])
    assert float(row.length) == pytest.approx(payload["length"])
    assert row.date_caught == datetime.fromisoformat(payload["date_caught"])


def test_patch_other_users_catch_returns_404_and_leaves_it_unmodified(client, db_session, make_user):
    user_a = make_user()
    user_b = make_user()

    payload = _full_payload()
    r_create = client.post("/catch/", json=payload, headers=user_a["headers"])
    assert r_create.status_code in (200, 201), r_create.text
    catch_id = r_create.json()["id"]

    r = client.patch(f"/catch/{catch_id}", json={"notes": "Hijacked"}, headers=user_b["headers"])

    assert r.status_code == 404

    row = db_session.get(Catch, catch_id)
    assert row.notes == payload["notes"]
    assert row.species == payload["species"]


# ---------------------------------------------------------------------------
# DELETE /catch/{catch_id}
# ---------------------------------------------------------------------------


def test_delete_own_catch_returns_204_and_removes_it(client, db_session, make_user):
    user = make_user()
    r_create = client.post("/catch/", json=_full_payload(), headers=user["headers"])
    assert r_create.status_code in (200, 201), r_create.text
    catch_id = r_create.json()["id"]

    r = client.delete(f"/catch/{catch_id}", headers=user["headers"])

    assert r.status_code == 204
    assert not r.content

    assert db_session.get(Catch, catch_id) is None

    r_get = client.get(f"/catch/{catch_id}", headers=user["headers"])
    assert r_get.status_code == 404


def test_delete_other_users_catch_returns_404_and_leaves_it_in_place(client, db_session, make_user):
    user_a = make_user()
    user_b = make_user()

    r_create = client.post("/catch/", json=_full_payload(), headers=user_a["headers"])
    assert r_create.status_code in (200, 201), r_create.text
    catch_id = r_create.json()["id"]

    r = client.delete(f"/catch/{catch_id}", headers=user_b["headers"])

    assert r.status_code == 404
    assert db_session.get(Catch, catch_id) is not None
