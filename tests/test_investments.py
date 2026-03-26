"""Integration tests for /api/investments."""

import pytest

INSTRUMENT_PAYLOAD = {"symbol": "AAPL", "name": "Apple Inc.", "asset_type": "stock"}

INVESTMENT_PAYLOAD = {
    "asset_symbol": "AAPL",
    "asset_name": "Apple Inc.",
    "asset_type": "stock",
    "quantity": 10.0,
    "purchase_price": 150.0,
    "purchase_date": "2025-01-15",
    "is_initial": False,
}

MOCK_PRICE = 200.0


@pytest.fixture(autouse=True)
def mock_yfinance(monkeypatch):
    monkeypatch.setattr(
        "src.api.endpoints.investments._fetch_current_price",
        lambda symbol: MOCK_PRICE,
    )


@pytest.fixture
def investment(client, account):
    payload = {**INVESTMENT_PAYLOAD, "source_account_id": account["id"]}
    return client.post("/api/investments", json=payload).json()


# ---------------------------------------------------------------------------
# Instruments
# ---------------------------------------------------------------------------


def test_list_instruments_empty(client):
    r = client.get("/api/investments/instruments")
    assert r.status_code == 200
    assert r.json() == []


def test_create_instrument(client):
    r = client.post("/api/investments/instruments", json=INSTRUMENT_PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["symbol"] == "AAPL"
    assert body["name"] == "Apple Inc."


def test_create_instrument_upserts(client):
    client.post("/api/investments/instruments", json=INSTRUMENT_PAYLOAD)
    r = client.post("/api/investments/instruments", json={**INSTRUMENT_PAYLOAD, "name": "Apple Actualizado"})
    assert r.status_code == 201
    assert r.json()["name"] == "Apple Actualizado"
    instruments = client.get("/api/investments/instruments").json()
    assert len(instruments) == 1


def test_create_instrument_uppercases_symbol(client):
    r = client.post("/api/investments/instruments", json={**INSTRUMENT_PAYLOAD, "symbol": "aapl"})
    assert r.json()["symbol"] == "AAPL"


# ---------------------------------------------------------------------------
# Investments CRUD
# ---------------------------------------------------------------------------


def test_list_investments_empty(client):
    r = client.get("/api/investments")
    assert r.status_code == 200
    assert r.json() == []


def test_create_investment(client, account):
    payload = {**INVESTMENT_PAYLOAD, "source_account_id": account["id"]}
    r = client.post("/api/investments", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["asset_symbol"] == "AAPL"
    assert body["quantity"] == 10.0
    assert body["current_price"] == MOCK_PRICE
    assert body["cost_basis"] == 1500.0
    assert body["current_value"] == 2000.0
    assert body["profit_loss"] == 500.0
    assert "id" in body


def test_list_investments_enriched(client, investment):
    r = client.get("/api/investments")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["current_price"] == MOCK_PRICE


def test_delete_investment(client, investment):
    r = client.delete(f"/api/investments/{investment['id']}")
    assert r.status_code == 204
    assert client.get("/api/investments").json() == []


def test_delete_investment_not_found(client):
    r = client.delete("/api/investments/99999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def test_summary_empty(client):
    r = client.get("/api/investments/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_invested"] == 0.0
    assert body["current_value"] == 0.0
    assert body["profit_loss"] == 0.0


def test_summary_with_investment(client, investment):
    r = client.get("/api/investments/summary")
    body = r.json()
    assert body["total_invested"] == 1500.0
    assert body["current_value"] == 2000.0
    assert body["profit_loss"] == 500.0


# ---------------------------------------------------------------------------
# By symbol
# ---------------------------------------------------------------------------


def test_by_symbol_empty(client):
    r = client.get("/api/investments/by-symbol")
    assert r.status_code == 200
    assert r.json() == []


def test_by_symbol_aggregates(client, account):
    payload = {**INVESTMENT_PAYLOAD, "source_account_id": account["id"]}
    client.post("/api/investments", json=payload)
    client.post("/api/investments", json={**payload, "quantity": 5.0, "purchase_price": 160.0})
    r = client.get("/api/investments/by-symbol")
    body = r.json()
    assert len(body) == 1
    assert body[0]["asset_symbol"] == "AAPL"
    assert body[0]["total_quantity"] == 15.0
    assert len(body[0]["purchases"]) == 2
