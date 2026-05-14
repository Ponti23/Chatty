import json
import httpx
from typing import AsyncGenerator
from app.embeddings import EmbeddingService
from app.vector_store import VectorStoreClient

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer questions based only on the provided context. "
    "If the context does not contain enough information, say so clearly."
)


async def stream_answer(
    tenant_id: str,
    query: str,
    history: list[dict],
    embeddings: EmbeddingService,
    vector_store: VectorStoreClient,
    ollama_base_url: str,
    model: str,
) -> AsyncGenerator[str, None]:
    query_vector = embeddings.embed_batch([query])[0]
    hits = vector_store.search(tenant_id, query_vector, top_k=5)

    context = "\n\n".join(
        f"[{h.payload.get('filename', 'doc')}]: {h.payload.get('text', '')}"
        for h in hits
    )

    user_message = f"Context:\n{context}\n\nQuestion: {query}" if context else query

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    payload = {"model": model, "messages": messages, "stream": True}

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", f"{ollama_base_url}/api/chat", json=payload) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = data.get("message", {}).get("content", "")
                if token:
                    yield token
                if data.get("done"):
                    break
