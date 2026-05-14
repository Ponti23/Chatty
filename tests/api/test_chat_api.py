# tests/api/test_chat_api.py
import pytest
import pytest_asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.auth import create_access_token

TENANT_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())


def _auth_headers() -> dict:
    token = create_access_token(USER_ID, TENANT_ID, "admin")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client():
    from app.main import app
    app.state.embeddings = MagicMock()
    app.state.embeddings.embed_batch.return_value = [[0.1] * 768]
    app.state.vector_store = MagicMock()
    app.state.vector_store.search.return_value = []
    app.state.storage = MagicMock()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_conversations_requires_auth(client):
    resp = await client.get("/api/v1/conversations")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_conversations_returns_list(client, db_session):
    resp = await client.get("/api/v1/conversations", headers=_auth_headers())
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
