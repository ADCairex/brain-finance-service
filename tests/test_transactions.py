"""Integration tests for /api/transactions."""

import pytest

EXPENSE = {
    "description": "Supermercado",
    "amount": 150.0,
    "category": "comida",
    "date": "2025-06-15",
    "is_income": False,
}

INCOME = {
    "description": "Sueldo",
    "amount": 3000.0,
    "category": "ingreso",
    "date": "2025-06-01",
    "is_income": True,
}


@pytest.fixture
def transaction(client, account):
    payload = {**EXPENSE, "account_id": account["id"]}
    return client.post("/api/transactions", json=payload).json()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def test_list_transactions_empty(client):
    r = client.get("/api/transactions")
    assert r.status_code == 200
    assert r.json() == []


def test_create_expense(client, account):
    r = client.post("/api/transactions", json={**EXPENSE, "account_id": account["id"]})
    assert r.status_code == 201
    body = r.json()
    assert body["description"] == EXPENSE["description"]
    assert body["is_income"] is False
    assert "id" in body


def test_create_income(client, account):
    r = client.post("/api/transactions", json={**INCOME, "account_id": account["id"]})
    assert r.status_code == 201
    assert r.json()["is_income"] is True


def test_get_transaction(client, transaction):
    r = client.get(f"/api/transactions/{transaction['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == transaction["id"]


def test_get_transaction_not_found(client):
    r = client.get("/api/transactions/99999")
    assert r.status_code == 404


def test_update_transaction(client, account, transaction):
    payload = {**EXPENSE, "account_id": account["id"], "description": "Actualizado", "amount": 999.0}
    r = client.put(f"/api/transactions/{transaction['id']}", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["description"] == "Actualizado"
    assert body["amount"] == 999.0


def test_update_transaction_not_found(client, account):
    r = client.put("/api/transactions/99999", json={**EXPENSE, "account_id": account["id"]})
    assert r.status_code == 404


def test_delete_transaction(client, transaction):
    r = client.delete(f"/api/transactions/{transaction['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/transactions/{transaction['id']}").status_code == 404


def test_delete_transaction_not_found(client):
    r = client.delete("/api/transactions/99999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------


def test_filter_by_is_income(client, account):
    client.post("/api/transactions", json={**EXPENSE, "account_id": account["id"]})
    client.post("/api/transactions", json={**INCOME, "account_id": account["id"]})
    r = client.get("/api/transactions?is_income=false")
    assert all(not t["is_income"] for t in r.json())


def test_filter_by_category(client, account):
    client.post("/api/transactions", json={**EXPENSE, "account_id": account["id"]})
    client.post("/api/transactions", json={**INCOME, "account_id": account["id"]})
    r = client.get("/api/transactions?category=comida")
    assert all(t["category"] == "comida" for t in r.json())


def test_filter_by_month_year(client, account):
    client.post("/api/transactions", json={**EXPENSE, "account_id": account["id"]})
    r = client.get("/api/transactions?month=6&year=2025")
    assert len(r.json()) == 1
    r_no_match = client.get("/api/transactions?month=1&year=2025")
    assert len(r_no_match.json()) == 0


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def test_summary_empty(client):
    r = client.get("/api/transactions/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_income"] == 0.0
    assert body["total_expenses"] == 0.0
    assert body["count"] == 0


def test_summary_with_transactions(client, account):
    client.post("/api/transactions", json={**INCOME, "account_id": account["id"]})
    client.post("/api/transactions", json={**EXPENSE, "account_id": account["id"]})
    r = client.get("/api/transactions/summary")
    body = r.json()
    assert body["total_income"] == 3000.0
    assert body["total_expenses"] == 150.0
    assert body["count"] == 2


# ---------------------------------------------------------------------------
# By category
# ---------------------------------------------------------------------------


def test_by_category_empty(client):
    r = client.get("/api/transactions/by-category")
    assert r.status_code == 200
    assert r.json() == []


def test_by_category_groups_expenses(client, account):
    client.post("/api/transactions", json={**EXPENSE, "account_id": account["id"]})
    client.post("/api/transactions", json={**EXPENSE, "amount": 50.0, "account_id": account["id"]})
    client.post("/api/transactions", json={**INCOME, "account_id": account["id"]})
    r = client.get("/api/transactions/by-category")
    body = r.json()
    assert len(body) == 1
    assert body[0]["category"] == "comida"
    assert body[0]["total"] == 200.0


# ---------------------------------------------------------------------------
# By month
# ---------------------------------------------------------------------------


def test_by_month_returns_12_months(client):
    r = client.get("/api/transactions/by-month?year=2025")
    assert r.status_code == 200
    assert len(r.json()) == 12


def test_by_month_aggregates_correctly(client, account):
    client.post("/api/transactions", json={**INCOME, "account_id": account["id"]})
    client.post("/api/transactions", json={**EXPENSE, "account_id": account["id"]})
    r = client.get("/api/transactions/by-month?year=2025")
    june = next(m for m in r.json() if m["month"] == 6)
    assert june["income"] == 3000.0
    assert june["expenses"] == 150.0
