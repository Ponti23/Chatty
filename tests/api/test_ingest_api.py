import pytest
import pytest_asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from app.repositories.sources import SourceRepository


TENANT_ID = str(uuid.uuid4())


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
            headers={"X-Tenant-ID": TENANT_ID},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert "source_id" in body
    assert body["status"] == "indexed"
    assert body["chunk_count"] > 0


@pytest.mark.asyncio
async def test_ingest_missing_file_and_url_returns_400(client):
    resp = await client.post(
        "/api/v1/sources",
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ingest_unsupported_type_returns_415(client):
    resp = await client.post(
        "/api/v1/sources",
        files={"file": ("data.xlsx", b"fakecontent", "application/vnd.ms-excel")},
        headers={"X-Tenant-ID": TENANT_ID},
    )
    assert resp.status_code == 415


@pytest.mark.asyncio
async def test_ingest_missing_tenant_header_returns_422(client):
    with open("tests/fixtures/sample.pdf", "rb") as f:
        resp = await client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
        )
    assert resp.status_code == 422
