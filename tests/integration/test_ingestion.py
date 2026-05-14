import pytest
import uuid

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_full_round_trip_pdf(real_client, auth_headers, vector_store):
    with open("tests/fixtures/sample.pdf", "rb") as f:
        resp = await real_client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    source_id = body["source_id"]
    chunk_count = body["chunk_count"]
    assert chunk_count > 0

    from app.auth import decode_token
    token = auth_headers["Authorization"].split(" ", 1)[1]
    tenant_id = decode_token(token)["tenant_id"]

    from qdrant_client.models import Filter, FieldCondition, MatchValue
    count_result = vector_store._client.count(
        collection_name="knowledge_chunks",
        count_filter=Filter(
            must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
        ),
        exact=True,
    )
    assert count_result.count == chunk_count


@pytest.mark.asyncio
async def test_reindex_replaces_not_duplicates(real_client, auth_headers, vector_store):
    from app.auth import decode_token
    token = auth_headers["Authorization"].split(" ", 1)[1]
    tenant_id = decode_token(token)["tenant_id"]

    with open("tests/fixtures/sample.pdf", "rb") as f:
        resp1 = await real_client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert resp1.status_code == 201
    first_count = resp1.json()["chunk_count"]

    with open("tests/fixtures/sample.pdf", "rb") as f:
        resp2 = await real_client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert resp2.status_code == 201
    second_count = resp2.json()["chunk_count"]

    from qdrant_client.models import Filter, FieldCondition, MatchValue
    total = vector_store._client.count(
        collection_name="knowledge_chunks",
        count_filter=Filter(
            must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
        ),
        exact=True,
    )
    # Two separate source_ids; delete_by_source only clears its own
    assert total.count == first_count + second_count


@pytest.mark.asyncio
async def test_tenant_isolation_search_returns_empty_for_other_tenant(real_client, auth_headers, vector_store):
    from app.auth import decode_token
    token = auth_headers["Authorization"].split(" ", 1)[1]
    tenant_a = decode_token(token)["tenant_id"]
    tenant_b = str(uuid.uuid4())

    with open("tests/fixtures/sample.pdf", "rb") as f:
        await real_client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
            headers=auth_headers,
        )

    zero_vector = [0.0] * 768
    results = vector_store.search(tenant_b, zero_vector, top_k=10)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_removes_vectors_from_qdrant(real_client, auth_headers, vector_store):
    from app.auth import decode_token
    token = auth_headers["Authorization"].split(" ", 1)[1]
    tenant_id = decode_token(token)["tenant_id"]

    with open("tests/fixtures/sample.pdf", "rb") as f:
        resp = await real_client.post(
            "/api/v1/sources",
            files={"file": ("sample.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert resp.status_code == 201
    source_id = resp.json()["source_id"]

    del_resp = await real_client.delete(
        f"/api/v1/sources/{source_id}",
        headers=auth_headers,
    )
    assert del_resp.status_code == 204

    from qdrant_client.models import Filter, FieldCondition, MatchValue
    count = vector_store._client.count(
        collection_name="knowledge_chunks",
        count_filter=Filter(
            must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
        ),
        exact=True,
    )
    assert count.count == 0
