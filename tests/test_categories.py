"""Integration tests for /api/categories."""


# ---------------------------------------------------------------------------
# Lazy seeding
# ---------------------------------------------------------------------------


def test_first_get_seeds_defaults(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 9
    names = [c["name"] for c in body]
    assert "comida" in names
    assert "casa" in names
    assert "otros" in names


def test_seed_is_idempotent(client):
    client.get("/api/categories")
    client.get("/api/categories")
    r = client.get("/api/categories")
    assert len(r.json()) == 9


def test_defaults_are_ordered_by_sort_order(client):
    r = client.get("/api/categories")
    body = r.json()
    assert body[0]["name"] == "comida"
    assert body[-1]["name"] == "otros"


def test_otros_is_not_deletable(client):
    r = client.get("/api/categories")
    otros = next(c for c in r.json() if c["name"] == "otros")
    assert otros["is_deletable"] is False
    assert otros["is_default"] is True


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_custom_category(client, categories):
    r = client.post(
        "/api/categories",
        json={
            "name": "mascotas",
            "label": "Mascotas",
            "emoji": "🐶",
            "color": "#ff9900",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "mascotas"
    assert body["is_default"] is False
    assert body["is_deletable"] is True


def test_create_duplicate_returns_409(client, categories):
    client.post(
        "/api/categories",
        json={
            "name": "mascotas",
            "label": "Mascotas",
            "emoji": "🐶",
            "color": "#ff9900",
        },
    )
    r = client.post(
        "/api/categories",
        json={
            "name": "mascotas",
            "label": "Mascotas 2",
            "emoji": "🐱",
            "color": "#ff0000",
        },
    )
    assert r.status_code == 409


def test_create_with_invalid_color_returns_422(client, categories):
    r = client.post(
        "/api/categories",
        json={
            "name": "test",
            "label": "Test",
            "emoji": "🔧",
            "color": "not-a-color",
        },
    )
    assert r.status_code == 422


def test_create_with_invalid_name_returns_422(client, categories):
    r = client.post(
        "/api/categories",
        json={
            "name": "Has Spaces",
            "label": "Test",
            "emoji": "🔧",
            "color": "#ff0000",
        },
    )
    assert r.status_code == 422


def test_create_assigns_next_sort_order(client, categories):
    r = client.post(
        "/api/categories",
        json={
            "name": "custom",
            "label": "Custom",
            "emoji": "⭐",
            "color": "#000000",
        },
    )
    assert r.json()["sort_order"] == 10  # 9 defaults + 1


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_category(client, categories):
    cat_id = categories[0]["id"]
    r = client.put(
        f"/api/categories/{cat_id}",
        json={
            "label": "Comida Actualizada",
            "emoji": "🍕",
        },
    )
    assert r.status_code == 200
    assert r.json()["label"] == "Comida Actualizada"
    assert r.json()["emoji"] == "🍕"
    # name should not change
    assert r.json()["name"] == "comida"


def test_update_not_found(client, categories):
    r = client.put("/api/categories/99999", json={"label": "Nope"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_custom_category(client, categories):
    # Create a custom category
    r = client.post(
        "/api/categories",
        json={
            "name": "temporal",
            "label": "Temporal",
            "emoji": "⏰",
            "color": "#123456",
        },
    )
    cat_id = r.json()["id"]
    r = client.delete(f"/api/categories/{cat_id}")
    assert r.status_code == 204


def test_delete_otros_returns_400(client, categories):
    otros = next(c for c in categories if c["name"] == "otros")
    r = client.delete(f"/api/categories/{otros['id']}")
    assert r.status_code == 400


def test_delete_reassigns_transactions(client, account, categories):
    # Create a custom category and a transaction using it
    client.post(
        "/api/categories",
        json={
            "name": "temporal",
            "label": "Temporal",
            "emoji": "⏰",
            "color": "#123456",
        },
    )
    client.post(
        "/api/transactions",
        json={
            "description": "Test",
            "amount": 50.0,
            "category": "temporal",
            "date": "2025-06-15",
            "is_income": False,
            "account_id": account["id"],
        },
    )

    # Delete the category
    cats = client.get("/api/categories").json()
    temporal = next(c for c in cats if c["name"] == "temporal")
    client.delete(f"/api/categories/{temporal['id']}")

    # Transaction should now have category "otros"
    txns = client.get("/api/transactions").json()
    assert txns[0]["category"] == "otros"


def test_delete_not_found(client, categories):
    r = client.delete("/api/categories/99999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Transaction validation
# ---------------------------------------------------------------------------


def test_transaction_with_invalid_category_returns_400(client, account, categories):
    r = client.post(
        "/api/transactions",
        json={
            "description": "Test",
            "amount": 50.0,
            "category": "no-existe",
            "date": "2025-06-15",
            "is_income": False,
            "account_id": account["id"],
        },
    )
    assert r.status_code == 400


def test_income_bypasses_category_validation(client, account, categories):
    r = client.post(
        "/api/transactions",
        json={
            "description": "Sueldo",
            "amount": 3000.0,
            "category": "whatever",
            "date": "2025-06-01",
            "is_income": True,
            "account_id": account["id"],
        },
    )
    assert r.status_code == 201
    assert r.json()["category"] == "ingreso"


# ---------------------------------------------------------------------------
# User isolation
# ---------------------------------------------------------------------------


def test_user_cannot_see_other_users_categories(client):
    # User 1 seeds
    client.get("/api/categories")

    # User 2 should get their own seeds, not user 1's
    from starlette.testclient import TestClient

    from src.api.app import app
    from src.api.database import get_db
    from tests.conftest import TestingSessionLocal

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-User-Id": "999"}) as c2:
        r = c2.get("/api/categories")
        assert len(r.json()) == 9
        # All categories belong to user 999
        assert all(c["user_id"] == 999 for c in r.json())
    app.dependency_overrides.clear()
