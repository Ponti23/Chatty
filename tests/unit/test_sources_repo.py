import pytest
import pytest_asyncio
import uuid
from app.repositories.sources import SourceRepository


TENANT_A = str(uuid.uuid4())
TENANT_B = str(uuid.uuid4())


@pytest.mark.asyncio
async def test_create_source(db_session):
    repo = SourceRepository(db_session)
    source_id = str(uuid.uuid4())
    source = await repo.create(TENANT_A, source_id, "doc.pdf", "pdf")

    assert str(source.source_id) == source_id
    assert str(source.tenant_id) == TENANT_A
    assert source.filename == "doc.pdf"
    assert source.source_type == "pdf"
    assert source.status == "indexing"


@pytest.mark.asyncio
async def test_update_status_to_indexed(db_session):
    repo = SourceRepository(db_session)
    source_id = str(uuid.uuid4())
    await repo.create(TENANT_A, source_id, "doc.pdf", "pdf")
    updated = await repo.update_status(source_id, "indexed", chunk_count=42)

    assert updated.status == "indexed"
    assert updated.chunk_count == 42


@pytest.mark.asyncio
async def test_update_status_to_failed(db_session):
    repo = SourceRepository(db_session)
    source_id = str(uuid.uuid4())
    await repo.create(TENANT_A, source_id, "bad.pdf", "pdf")
    updated = await repo.update_status(source_id, "failed", error_message="parse error")

    assert updated.status == "failed"
    assert updated.error_message == "parse error"


@pytest.mark.asyncio
async def test_get_by_tenant_only_returns_own_sources(db_session):
    repo = SourceRepository(db_session)
    sid_a = str(uuid.uuid4())
    sid_b = str(uuid.uuid4())
    await repo.create(TENANT_A, sid_a, "a.pdf", "pdf")
    await repo.create(TENANT_B, sid_b, "b.pdf", "pdf")

    results = await repo.get_by_tenant(TENANT_A)
    source_ids = [str(s.source_id) for s in results]
    assert sid_a in source_ids
    assert sid_b not in source_ids


@pytest.mark.asyncio
async def test_delete_source(db_session):
    repo = SourceRepository(db_session)
    source_id = str(uuid.uuid4())
    await repo.create(TENANT_A, source_id, "doc.pdf", "pdf")
    await repo.delete(source_id)

    results = await repo.get_by_tenant(TENANT_A)
    assert not any(str(s.source_id) == source_id for s in results)


@pytest.mark.asyncio
async def test_update_status_raises_for_missing_source(db_session):
    repo = SourceRepository(db_session)
    with pytest.raises(ValueError, match="not found"):
        await repo.update_status(str(uuid.uuid4()), "indexed", chunk_count=1)
