import pytest
import pytest_asyncio
import uuid
from unittest.mock import MagicMock
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

    mock_embeddings = MagicMock()
    mock_embeddings.embed_batch.return_value = [[0.1] * 768]

    mock_vector_store = MagicMock()
    mock_storage = MagicMock()

    app.state.embeddings = mock_embeddings
    app.state.vector_store = mock_vector_store
    app.state.storage = mock_storage

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_ingest_pdf_returns_201(client, db_session):
    with open("tests/fixtures/sample.pdf", "rb") as f:
        resp = await client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
            headers=_auth_headers(),
        )
    assert resp.status_code == 201
    body = resp.json()
    assert "source_id" in body
    assert body["status"] == "indexed"
    assert body["chunk_count"] > 0


@pytest.mark.asyncio
async def test_ingest_missing_file_and_url_returns_400(client):
    resp = await client.post("/api/v1/sources", headers=_auth_headers())
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ingest_unsupported_type_returns_415(client):
    resp = await client.post(
        "/api/v1/sources",
        files={"file": ("data.xlsx", b"fakecontent", "application/vnd.ms-excel")},
        headers=_auth_headers(),
    )
    assert resp.status_code == 415


@pytest.mark.asyncio
async def test_ingest_missing_auth_returns_401(client):
    with open("tests/fixtures/sample.pdf", "rb") as f:
        resp = await client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_delete_source_returns_204(client):
    with open("tests/fixtures/sample.pdf", "rb") as f:
        post_resp = await client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
            headers=_auth_headers(),
        )
    assert post_resp.status_code == 201
    source_id = post_resp.json()["source_id"]

    resp = await client.delete(
        f"/api/v1/sources/{source_id}",
        headers=_auth_headers(),
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_calls_vector_store_and_storage(client):
    from app.main import app as fastapi_app

    with open("tests/fixtures/sample.pdf", "rb") as f:
        post_resp = await client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
            headers=_auth_headers(),
        )
    assert post_resp.status_code == 201
    source_id = post_resp.json()["source_id"]

    resp = await client.delete(
        f"/api/v1/sources/{source_id}",
        headers=_auth_headers(),
    )
    assert resp.status_code == 204
    fastapi_app.state.vector_store.delete_by_source.assert_called_with(TENANT_ID, source_id)
    fastapi_app.state.storage.delete.assert_called_once()
