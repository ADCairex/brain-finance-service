"""Integration tests for /api/assets."""

import pytest

ASSET_PAYLOAD = {
    "name": "Notebook",
    "value": 1200.0,
    "category": "electronico",
    "acquisition_date": "2024-03-10",
    "is_initial": False,
}


@pytest.fixture
def asset(client, account):
    payload = {**ASSET_PAYLOAD, "account_id": account["id"]}
    return client.post("/api/assets", json=payload).json()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def test_list_assets_empty(client):
    r = client.get("/api/assets")
    assert r.status_code == 200
    assert r.json() == []


def test_create_asset(client, account):
    r = client.post("/api/assets", json={**ASSET_PAYLOAD, "account_id": account["id"]})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == ASSET_PAYLOAD["name"]
    assert body["value"] == ASSET_PAYLOAD["value"]
    assert body["category"] == ASSET_PAYLOAD["category"]
    assert "id" in body


def test_create_asset_default_category(client, account):
    payload = {"name": "Cosa", "value": 100.0, "acquisition_date": "2024-01-01", "account_id": account["id"]}
    r = client.post("/api/assets", json=payload)
    assert r.status_code == 201
    assert r.json()["category"] == "otro"


def test_list_assets_returns_created(client, account):
    client.post("/api/assets", json={**ASSET_PAYLOAD, "account_id": account["id"]})
    client.post("/api/assets", json={**ASSET_PAYLOAD, "name": "Celular", "account_id": account["id"]})
    r = client.get("/api/assets")
    assert len(r.json()) == 2


def test_get_asset(client, asset):
    r = client.get(f"/api/assets/{asset['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == asset["id"]


def test_get_asset_not_found(client):
    r = client.get("/api/assets/99999")
    assert r.status_code == 404


def test_update_asset(client, account, asset):
    payload = {**ASSET_PAYLOAD, "account_id": account["id"], "name": "Actualizado", "value": 9999.0}
    r = client.put(f"/api/assets/{asset['id']}", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Actualizado"
    assert body["value"] == 9999.0


def test_update_asset_not_found(client, account):
    r = client.put("/api/assets/99999", json={**ASSET_PAYLOAD, "account_id": account["id"]})
    assert r.status_code == 404


def test_delete_asset(client, asset):
    r = client.delete(f"/api/assets/{asset['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/assets/{asset['id']}").status_code == 404


def test_delete_asset_not_found(client):
    r = client.delete("/api/assets/99999")
    assert r.status_code == 404


def test_user_isolation(client, account):
    client.post("/api/assets", json={**ASSET_PAYLOAD, "account_id": account["id"]})
    r = client.get("/api/assets", headers={"X-User-Id": "2"})
    assert r.json() == []
