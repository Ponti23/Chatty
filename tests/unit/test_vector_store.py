from unittest.mock import MagicMock, patch
from app.vector_store import VectorStoreClient
from app.chunking import Chunk


TENANT_A = "tenant-aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa"
TENANT_B = "tenant-bbbbbbbb-0000-0000-0000-bbbbbbbbbbbb"
SOURCE_ID = "source-cccccccc-0000-0000-0000-cccccccccccc"


def make_client():
    with patch("app.vector_store.QdrantClient"):
        client = VectorStoreClient("localhost", 6333)
    return client


def test_upsert_sets_tenant_id_on_all_points():
    client = make_client()
    chunks = [
        Chunk(text="chunk one", source_id=SOURCE_ID, chunk_index=0, metadata={}),
        Chunk(text="chunk two", source_id=SOURCE_ID, chunk_index=1, metadata={}),
    ]
    vectors = [[0.1] * 768, [0.2] * 768]

    client.upsert_chunks(TENANT_A, chunks, vectors)

    call_kwargs = client._client.upsert.call_args[1]
    points = call_kwargs["points"]
    assert len(points) == 2
    assert all(p.payload["tenant_id"] == TENANT_A for p in points)


def test_upsert_sets_source_id_on_all_points():
    client = make_client()
    chunks = [Chunk(text="text", source_id=SOURCE_ID, chunk_index=0, metadata={})]
    vectors = [[0.1] * 768]

    client.upsert_chunks(TENANT_A, chunks, vectors)

    points = client._client.upsert.call_args[1]["points"]
    assert points[0].payload["source_id"] == SOURCE_ID


def test_search_always_filters_by_tenant_id():
    client = make_client()
    client.search(TENANT_A, [0.1] * 768, top_k=5)

    call_kwargs = client._client.search.call_args[1]
    filter_conditions = call_kwargs["query_filter"].must
    tenant_condition = next(f for f in filter_conditions if f.key == "tenant_id")
    assert tenant_condition.match.value == TENANT_A


def test_search_with_different_tenants_uses_different_filters():
    client = make_client()
    client.search(TENANT_A, [0.1] * 768, top_k=5)
    client.search(TENANT_B, [0.1] * 768, top_k=5)

    calls = client._client.search.call_args_list
    filter_a = next(f for f in calls[0][1]["query_filter"].must if f.key == "tenant_id")
    filter_b = next(f for f in calls[1][1]["query_filter"].must if f.key == "tenant_id")
    assert filter_a.match.value == TENANT_A
    assert filter_b.match.value == TENANT_B


def test_delete_by_source_filters_by_both_tenant_and_source():
    client = make_client()
    client.delete_by_source(TENANT_A, SOURCE_ID)

    call_kwargs = client._client.delete.call_args[1]
    conditions = call_kwargs["points_selector"].must
    keys = {f.key: f.match.value for f in conditions}
    assert keys["tenant_id"] == TENANT_A
    assert keys["source_id"] == SOURCE_ID
