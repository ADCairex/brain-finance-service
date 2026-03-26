"""Integration tests for /api/accounts."""


def test_list_accounts_empty(client):
    r = client.get("/api/accounts")
    assert r.status_code == 200
    assert r.json() == []


def test_create_account(client):
    r = client.post("/api/accounts", json={"name": "Ahorro", "initial_balance": 500.0})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Ahorro"
    assert body["initial_balance"] == 500.0
    assert "id" in body


def test_create_account_default_balance(client):
    r = client.post("/api/accounts", json={"name": "Sin saldo"})
    assert r.status_code == 201
    assert r.json()["initial_balance"] == 0.0


def test_list_accounts_returns_created(client):
    client.post("/api/accounts", json={"name": "Cuenta A", "initial_balance": 100.0})
    client.post("/api/accounts", json={"name": "Cuenta B", "initial_balance": 200.0})
    r = client.get("/api/accounts")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_account(client, account):
    r = client.get(f"/api/accounts/{account['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == account["id"]


def test_get_account_not_found(client):
    r = client.get("/api/accounts/99999")
    assert r.status_code == 404


def test_update_account(client, account):
    r = client.put(f"/api/accounts/{account['id']}", json={"name": "Actualizada", "initial_balance": 9999.0})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Actualizada"
    assert body["initial_balance"] == 9999.0


def test_update_account_not_found(client):
    r = client.put("/api/accounts/99999", json={"name": "X", "initial_balance": 0.0})
    assert r.status_code == 404


def test_delete_account(client, account):
    r = client.delete(f"/api/accounts/{account['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/accounts/{account['id']}").status_code == 404


def test_delete_account_not_found(client):
    r = client.delete("/api/accounts/99999")
    assert r.status_code == 404


def test_user_isolation(client):
    client.post("/api/accounts", json={"name": "Mi cuenta", "initial_balance": 100.0})
    other = client.get("/api/accounts", headers={"X-User-Id": "2"})
    assert other.json() == []
