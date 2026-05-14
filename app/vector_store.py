import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
)
from app.chunking import Chunk

COLLECTION_NAME = "knowledge_chunks"
VECTOR_SIZE = 768


class VectorStoreClient:
    def __init__(self, host: str, port: int):
        self._client = QdrantClient(host=host, port=port)

    def ensure_collection(self) -> None:
        existing = {c.name for c in self._client.get_collections().collections}
        if COLLECTION_NAME not in existing:
            self._client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def upsert_chunks(self, tenant_id: str, chunks: list[Chunk], vectors: list[list[float]]) -> int:
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "tenant_id": tenant_id,
                    "source_id": chunk.source_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    **chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        self._client.upsert(collection_name=COLLECTION_NAME, points=points)
        return len(points)

    def delete_by_source(self, tenant_id: str, source_id: str) -> None:
        self._client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
                    FieldCondition(key="source_id", match=MatchValue(value=source_id)),
                ]
            ),
        )

    def search(self, tenant_id: str, query_vector: list[float], top_k: int = 5):
        return self._client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(
                must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
            ),
            limit=top_k,
            with_payload=True,
        )
