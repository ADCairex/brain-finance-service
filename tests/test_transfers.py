"""Integration tests for /api/transfers."""

import pytest


@pytest.fixture
def two_accounts(client):
    a = client.post("/api/accounts", json={"name": "Cuenta A", "initial_balance": 1000.0}).json()
    b = client.post("/api/accounts", json={"name": "Cuenta B", "initial_balance": 500.0}).json()
    return a, b


@pytest.fixture
def transfer(client, two_accounts):
    a, b = two_accounts
    r = client.post(
        "/api/transfers",
        json={
            "from_account_id": a["id"],
            "to_account_id": b["id"],
            "amount": 200.0,
            "date": "2025-06-15",
            "description": "Pago cuota",
        },
    )
    return r.json()


def test_list_transfers_empty(client):
    r = client.get("/api/transfers")
    assert r.status_code == 200
    assert r.json() == []


def test_create_transfer(client, two_accounts):
    a, b = two_accounts
    r = client.post(
        "/api/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": 100.0, "date": "2025-06-01"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["from_account_id"] == a["id"]
    assert body["to_account_id"] == b["id"]
    assert body["amount"] == 100.0
    assert body["date"] == "2025-06-01"
    assert body["description"] is None
    assert "id" in body


def test_create_transfer_with_description(client, two_accounts):
    a, b = two_accounts
    r = client.post(
        "/api/transfers",
        json={
            "from_account_id": a["id"],
            "to_account_id": b["id"],
            "amount": 50.0,
            "date": "2025-07-01",
            "description": "Ahorro mensual",
        },
    )
    assert r.status_code == 201
    assert r.json()["description"] == "Ahorro mensual"


def test_list_transfers_returns_created(client, transfer):
    r = client.get("/api/transfers")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == transfer["id"]


def test_get_transfer(client, transfer):
    r = client.get(f"/api/transfers/{transfer['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == transfer["id"]


def test_get_transfer_not_found(client):
    r = client.get("/api/transfers/99999")
    assert r.status_code == 404


def test_update_transfer(client, transfer, two_accounts):
    a, b = two_accounts
    r = client.put(
        f"/api/transfers/{transfer['id']}",
        json={
            "from_account_id": a["id"],
            "to_account_id": b["id"],
            "amount": 999.0,
            "date": "2025-08-01",
            "description": "Actualizada",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["amount"] == 999.0
    assert body["description"] == "Actualizada"


def test_update_transfer_not_found(client, two_accounts):
    a, b = two_accounts
    r = client.put(
        "/api/transfers/99999",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": 1.0, "date": "2025-01-01"},
    )
    assert r.status_code == 404


def test_delete_transfer(client, transfer):
    r = client.delete(f"/api/transfers/{transfer['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/transfers/{transfer['id']}").status_code == 404


def test_delete_transfer_not_found(client):
    r = client.delete("/api/transfers/99999")
    assert r.status_code == 404


def test_filter_by_account_id(client, two_accounts):
    a, b = two_accounts
    c = client.post("/api/accounts", json={"name": "Cuenta C", "initial_balance": 0.0}).json()

    client.post(
        "/api/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": 100.0, "date": "2025-01-01"},
    )
    client.post(
        "/api/transfers",
        json={"from_account_id": b["id"], "to_account_id": c["id"], "amount": 50.0, "date": "2025-01-01"},
    )

    # a is only in first transfer (as source)
    r = client.get(f"/api/transfers?account_id={a['id']}")
    assert len(r.json()) == 1

    # b is in both transfers
    r = client.get(f"/api/transfers?account_id={b['id']}")
    assert len(r.json()) == 2


def test_filter_by_year(client, two_accounts):
    a, b = two_accounts
    client.post(
        "/api/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": 100.0, "date": "2024-03-01"},
    )
    client.post(
        "/api/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": 200.0, "date": "2025-03-01"},
    )

    r = client.get("/api/transfers?year=2025")
    assert len(r.json()) == 1
    assert r.json()[0]["amount"] == 200.0


def test_filter_by_month(client, two_accounts):
    a, b = two_accounts
    client.post(
        "/api/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": 100.0, "date": "2025-01-15"},
    )
    client.post(
        "/api/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": 200.0, "date": "2025-06-15"},
    )

    r = client.get("/api/transfers?month=6")
    assert len(r.json()) == 1
    assert r.json()[0]["amount"] == 200.0


def test_user_isolation(client, two_accounts):
    a, b = two_accounts
    client.post(
        "/api/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": 100.0, "date": "2025-01-01"},
    )

    r = client.get("/api/transfers", headers={"X-User-Id": "2"})
    assert r.json() == []
