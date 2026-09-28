"""Tests for the Lure table and its endpoints (routers/lures.py).

Uses the shared fixtures from conftest.py: `client`, `db_session`, and
`make_user`. Every lure is created for a throwaway user obtained via
`make_user()`, whose auto-cleanup deletes the user's lures (and catches)
afterwards, so tests don't need to clean up lures by hand.
"""

from decimal import Decimal

from models import Lure


# ---------------------------------------------------------------------------
# POST /lure/
# ---------------------------------------------------------------------------


def test_create_lure_full_fields_persists_and_returns_correct_data(client, db_session, make_user):
    user = make_user()

    payload = {
        "name": "Deep Diver",
        "weight": "12.50",
        "type": "crankbait",
        "color": "chartreuse",
        "brand": "Rapala",
        "model": "DT-10",
        "size": "3.50",
    }

    r = client.post("/lure/", json=payload, headers=user["headers"])

    assert r.status_code in (200, 201)
    body = r.json()

    assert body["user_id"] == user["id"]
    assert body["name"] == payload["name"]
    assert body["type"] == payload["type"]
    assert body["color"] == payload["color"]
    assert body["brand"] == payload["brand"]
    assert body["model"] == payload["model"]
    assert Decimal(str(body["weight"])) == Decimal(payload["weight"])
    assert Decimal(str(body["size"])) == Decimal(payload["size"])

    row = db_session.get(Lure, body["id"])
    assert row is not None
    assert row.user_id == user["id"]
    assert row.name == payload["name"]
    assert row.type == payload["type"]
    assert row.color == payload["color"]
    assert row.brand == payload["brand"]
    assert row.model == payload["model"]
    assert row.weight == Decimal(payload["weight"])
    assert row.size == Decimal(payload["size"])


def test_create_lure_with_omitted_optional_fields_succeeds_with_nulls(client, db_session, make_user):
    user = make_user()

    r = client.post("/lure/", json={}, headers=user["headers"])

    assert r.status_code in (200, 201)
    body = r.json()

    assert body["user_id"] == user["id"]
    assert body["name"] is None
    assert body["weight"] is None
    assert body["type"] is None
    assert body["color"] is None
    assert body["brand"] is None
    assert body["model"] is None
    assert body["size"] is None

    row = db_session.get(Lure, body["id"])
    assert row is not None
    assert row.user_id == user["id"]
    assert row.name is None
    assert row.weight is None
    assert row.type is None
    assert row.color is None
    assert row.brand is None
    assert row.model is None
    assert row.size is None


def test_create_lure_without_auth_header_returns_401(client):
    r = client.post("/lure/", json={"name": "No Auth Lure"})

    assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /lure/
# ---------------------------------------------------------------------------


def test_list_lures_returns_exactly_the_caller_own_lures(client, make_user):
    user = make_user()

    payload_a = {"name": "Lure A", "type": "spinnerbait"}
    payload_b = {"name": "Lure B", "type": "jig"}

    r1 = client.post("/lure/", json=payload_a, headers=user["headers"])
    r2 = client.post("/lure/", json=payload_b, headers=user["headers"])
    assert r1.status_code in (200, 201)
    assert r2.status_code in (200, 201)
    id_a, id_b = r1.json()["id"], r2.json()["id"]

    r = client.get("/lure/", headers=user["headers"])

    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2

    ids = {item["id"] for item in body}
    assert ids == {id_a, id_b}

    by_id = {item["id"]: item for item in body}
    assert by_id[id_a]["name"] == "Lure A"
    assert by_id[id_a]["type"] == "spinnerbait"
    assert by_id[id_a]["user_id"] == user["id"]
    assert by_id[id_b]["name"] == "Lure B"
    assert by_id[id_b]["type"] == "jig"
    assert by_id[id_b]["user_id"] == user["id"]


def test_list_lures_as_different_user_does_not_include_others_lures(client, make_user):
    user_a = make_user()
    user_b = make_user()

    r = client.post("/lure/", json={"name": "Only A's Lure"}, headers=user_a["headers"])
    assert r.status_code in (200, 201)

    r = client.get("/lure/", headers=user_b["headers"])

    assert r.status_code == 200
    body = r.json()
    assert body == []


# ---------------------------------------------------------------------------
# GET /lure/{lure_id}
# ---------------------------------------------------------------------------


def test_get_own_lure_returns_correct_fields(client, make_user):
    user = make_user()

    payload = {"name": "Topwater Popper", "type": "popper", "brand": "Heddon"}
    r = client.post("/lure/", json=payload, headers=user["headers"])
    assert r.status_code in (200, 201)
    lure_id = r.json()["id"]

    r = client.get(f"/lure/{lure_id}", headers=user["headers"])

    assert r.status_code == 200
    body = r.json()
    assert body["id"] == lure_id
    assert body["user_id"] == user["id"]
    assert body["name"] == payload["name"]
    assert body["type"] == payload["type"]
    assert body["brand"] == payload["brand"]


def test_get_lure_as_non_owner_returns_404(client, make_user):
    user_a = make_user()
    user_b = make_user()

    r = client.post("/lure/", json={"name": "A's Lure"}, headers=user_a["headers"])
    assert r.status_code in (200, 201)
    lure_id = r.json()["id"]

    r = client.get(f"/lure/{lure_id}", headers=user_b["headers"])

    assert r.status_code == 404


def test_get_nonexistent_lure_returns_404_same_shape_as_non_owner(client, make_user):
    user_a = make_user()
    user_b = make_user()

    r = client.post("/lure/", json={"name": "A's Lure"}, headers=user_a["headers"])
    assert r.status_code in (200, 201)
    lure_id = r.json()["id"]

    r_missing = client.get("/lure/999999999", headers=user_a["headers"])
    assert r_missing.status_code == 404

    r_not_owned = client.get(f"/lure/{lure_id}", headers=user_b["headers"])
    assert r_not_owned.status_code == 404

    # existence of the id shouldn't be distinguishable from the response body
    assert r_missing.json() == r_not_owned.json()


# ---------------------------------------------------------------------------
# PATCH /lure/{lure_id}
# ---------------------------------------------------------------------------


def test_patch_one_field_changes_only_that_field(client, db_session, make_user):
    user = make_user()

    payload = {
        "name": "Original Name",
        "weight": "5.00",
        "type": "spoon",
        "color": "silver",
        "brand": "Original Brand",
        "model": "Original Model",
        "size": "2.00",
    }
    r = client.post("/lure/", json=payload, headers=user["headers"])
    assert r.status_code in (200, 201)
    lure_id = r.json()["id"]

    r = client.patch(f"/lure/{lure_id}", json={"name": "Updated Name"}, headers=user["headers"])

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Updated Name"
    assert body["color"] == payload["color"]
    assert body["brand"] == payload["brand"]
    assert body["model"] == payload["model"]
    assert body["type"] == payload["type"]

    db_session.expire_all()
    row = db_session.get(Lure, lure_id)
    assert row.name == "Updated Name"
    assert row.weight == Decimal(payload["weight"])
    assert row.type == payload["type"]
    assert row.color == payload["color"]
    assert row.brand == payload["brand"]
    assert row.model == payload["model"]
    assert row.size == Decimal(payload["size"])


def test_patch_lure_as_non_owner_returns_404_and_does_not_modify(client, db_session, make_user):
    user_a = make_user()
    user_b = make_user()

    payload = {"name": "A's Original Name", "brand": "A's Brand"}
    r = client.post("/lure/", json=payload, headers=user_a["headers"])
    assert r.status_code in (200, 201)
    lure_id = r.json()["id"]

    r = client.patch(f"/lure/{lure_id}", json={"name": "Hijacked Name"}, headers=user_b["headers"])

    assert r.status_code == 404

    db_session.expire_all()
    row = db_session.get(Lure, lure_id)
    assert row.name == payload["name"]
    assert row.brand == payload["brand"]


# ---------------------------------------------------------------------------
# DELETE /lure/{lure_id}
# ---------------------------------------------------------------------------


def test_delete_own_lure_removes_it_from_database(client, db_session, make_user):
    user = make_user()

    r = client.post("/lure/", json={"name": "To Be Deleted"}, headers=user["headers"])
    assert r.status_code in (200, 201)
    lure_id = r.json()["id"]

    r = client.delete(f"/lure/{lure_id}", headers=user["headers"])
    assert r.status_code == 204
    assert not r.content

    db_session.expire_all()
    assert db_session.get(Lure, lure_id) is None

    r_get = client.get(f"/lure/{lure_id}", headers=user["headers"])
    assert r_get.status_code == 404


def test_delete_lure_as_non_owner_returns_404_and_does_not_delete(client, db_session, make_user):
    user_a = make_user()
    user_b = make_user()

    r = client.post("/lure/", json={"name": "A's Lure To Keep"}, headers=user_a["headers"])
    assert r.status_code in (200, 201)
    lure_id = r.json()["id"]

    r = client.delete(f"/lure/{lure_id}", headers=user_b["headers"])
    assert r.status_code == 404

    db_session.expire_all()
    row = db_session.get(Lure, lure_id)
    assert row is not None
    assert row.name == "A's Lure To Keep"
