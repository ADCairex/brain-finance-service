import os

# MUST be set BEFORE any src imports — modules execute at import time
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.app import app
from src.api.database import Base, get_db

TEST_DB_URL = "sqlite:///./test.db"
USER_ID = "1"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True, headers={"X-User-Id": USER_ID}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def account(client):
    r = client.post("/api/accounts", json={"name": "Cuenta principal", "initial_balance": 1000.0})
    return r.json()


@pytest.fixture
def categories(client):
    """Seed default categories by calling GET /api/categories (lazy seeding)."""
    r = client.get("/api/categories")
    return r.json()
