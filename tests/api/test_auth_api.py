# tests/api/test_auth_api.py
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest_asyncio.fixture
async def client():
    from app.main import app
    from unittest.mock import MagicMock
    app.state.embeddings = MagicMock()
    app.state.vector_store = MagicMock()
    app.state.storage = MagicMock()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_creates_user_and_returns_token(client, db_session):
    email = f"admin-{uuid.uuid4()}@acme.com"
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "tenant_name": f"Acme-{uuid.uuid4()}"
    })
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_returns_token(client, db_session):
    email = f"user-{uuid.uuid4()}@acme.com"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "tenant_name": f"Acme-{uuid.uuid4()}"
    })
    resp = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "Password123!"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client, db_session):
    email = f"other-{uuid.uuid4()}@acme.com"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "tenant_name": f"Acme-{uuid.uuid4()}"
    })
    resp = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "WrongPassword"
    })
    assert resp.status_code == 401
