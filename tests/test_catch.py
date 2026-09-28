"""Tests for the Catch table and its endpoints (routers/catches.py).

Uses the shared fixtures from conftest.py: `client`, `db_session`, and
`make_user`. Every catch needs an owning user, so `make_user()` is used for
every test - it also cleans up any catches (and lures) that user owns.

Note: `date_caught` is always passed explicitly below (rather than relying
on `CatchCreate`'s default) so tests are deterministic.

`Catch.date_caught` is a timezone-aware column (`DateTime(timezone=True)`,
see AGENTS.md's 2026-09-28 log entry). The payloads below send *naive* ISO
strings (no offset); Postgres interprets a naive value written to a
`timestamptz` column as being in the session's timezone, tagging it with
that offset on the way back out rather than shifting the wall-clock digits.
So the correct round-trip check is "same wall-clock digits, now
offset-tagged" - not an exact naive-vs-aware equality (which raises/always
mismatches) and not exact-string comparison (the offset returned depends on
the session's timezone GUC, not necessarily `Z`/`+00:00`). See
`_assert_same_wall_clock` below.
"""

from datetime import datetime

import httpx
import pytest

import clients.open_meteo as open_meteo
from models import Catch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_same_wall_clock(actual: datetime, expected_iso: str) -> None:
    """Assert `actual` (a timezone-aware datetime from the DB or API
    response) has the same wall-clock digits as `expected_iso` (the naive
    ISO string originally sent), ignoring whatever offset Postgres tagged
    it with. This is the fixed-bug invariant: previously the digits
    themselves shifted by the server's UTC offset on round-trip; now they
    don't, they're just correctly tagged with an explicit offset instead of
    being ambiguously naive.
    """
    assert actual.tzinfo is not None, "expected a timezone-aware datetime"
    assert actual.replace(tzinfo=None) == datetime.fromisoformat(expected_iso)


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
    _assert_same_wall_clock(row.date_caught, payload["date_caught"])
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
    _assert_same_wall_clock(row.date_caught, payload["date_caught"])
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
    _assert_same_wall_clock(datetime.fromisoformat(body["date_caught"]), payload["date_caught"])


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
    _assert_same_wall_clock(row.date_caught, payload["date_caught"])


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


# ---------------------------------------------------------------------------
# POST /catch/ - Open-Meteo weather snapshot integration
#
# `clients/open_meteo.py`'s internal `_fetch()` is monkeypatched to control
# what Open-Meteo "returns" without ever making a real HTTP call. This still
# exercises `get_weather_snapshot()`'s own parsing/fallback logic for real -
# only the actual network hop is replaced.
# ---------------------------------------------------------------------------


async def _fake_fetch_success(base_url, path, params):
    """Stands in for a real Open-Meteo forecast response. `date_caught` in
    the tests below is 2026-05-01T10:30:00, so the closest hourly reading is
    deliberately the 10:00 entry (a 30-minute gap beats the 09:00 entry's
    90-minute gap; the 11:00 entry ties at 30 minutes but the lookup keeps
    the first-seen match on ties)."""
    return {
        "hourly": {
            "time": ["2026-05-01T09:00", "2026-05-01T10:00", "2026-05-01T11:00"],
            "temperature_2m": [18.5, 20.1, 21.3],
            "weathercode": [1, 2, 3],
        },
        "daily": {
            "sunrise": ["2026-05-01T06:15"],
            "sunset": ["2026-05-01T18:05"],
        },
    }


async def _fake_fetch_always_fails(base_url, path, params):
    raise httpx.ConnectError("simulated network failure")


async def _fail_if_weather_lookup_is_attempted(*args, **kwargs):
    raise AssertionError(
        "get_weather_snapshot() should never be called when latitude/longitude are missing"
    )


def test_create_catch_with_coordinates_and_successful_weather_lookup_populates_snapshot(
    client, db_session, make_user, monkeypatch
):
    monkeypatch.setattr(open_meteo, "_fetch", _fake_fetch_success)
    user = make_user()
    payload = _full_payload(date_caught="2026-05-01T10:30:00")

    r = client.post("/catch/", json=payload, headers=user["headers"])

    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body["temperature"] == pytest.approx(20.1)
    assert body["conditions"] == "Partly cloudy"
    assert body["sunrise"] == "2026-05-01T06:15:00"
    assert body["sunset"] == "2026-05-01T18:05:00"

    row = db_session.get(Catch, body["id"])
    assert row is not None
    assert float(row.temperature) == pytest.approx(20.1)
    assert row.conditions == "Partly cloudy"
    assert row.sunrise == datetime(2026, 5, 1, 6, 15)
    assert row.sunset == datetime(2026, 5, 1, 18, 5)


def test_create_catch_without_coordinates_skips_weather_lookup_entirely(
    client, db_session, make_user, monkeypatch
):
    monkeypatch.setattr(
        "routers.catches.get_weather_snapshot", _fail_if_weather_lookup_is_attempted
    )
    user = make_user()
    payload = _full_payload(latitude=None, longitude=None)

    r = client.post("/catch/", json=payload, headers=user["headers"])

    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body["latitude"] is None
    assert body["longitude"] is None
    for field in ("temperature", "conditions", "sunrise", "sunset"):
        assert body.get(field) is None

    row = db_session.get(Catch, body["id"])
    assert row is not None
    assert row.latitude is None
    assert row.longitude is None
    assert row.temperature is None
    assert row.conditions is None
    assert row.sunrise is None
    assert row.sunset is None


def test_create_catch_with_coordinates_and_failed_weather_lookup_still_persists_catch(
    client, db_session, make_user, monkeypatch
):
    monkeypatch.setattr(open_meteo, "_fetch", _fake_fetch_always_fails)
    user = make_user()
    payload = _full_payload(date_caught="2026-05-01T10:30:00")

    r = client.post("/catch/", json=payload, headers=user["headers"])

    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body["species"] == payload["species"]
    for field in ("temperature", "conditions", "sunrise", "sunset"):
        assert body.get(field) is None

    row = db_session.get(Catch, body["id"])
    assert row is not None
    assert row.species == payload["species"]
    assert row.temperature is None
    assert row.conditions is None
    assert row.sunrise is None
    assert row.sunset is None
