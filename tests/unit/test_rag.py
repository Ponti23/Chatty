# tests/unit/test_rag.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json


@pytest.mark.asyncio
async def test_stream_answer_yields_tokens():
    from app.rag import stream_answer

    mock_embeddings = MagicMock()
    mock_embeddings.embed_batch.return_value = [[0.1] * 768]

    mock_vector_store = MagicMock()
    mock_vector_store.search.return_value = [
        MagicMock(payload={"text": "Relevant context chunk.", "filename": "doc.pdf"})
    ]

    ollama_lines = [
        json.dumps({"message": {"content": "Hello"}, "done": False}),
        json.dumps({"message": {"content": " world"}, "done": False}),
        json.dumps({"message": {"content": ""}, "done": True}),
    ]

    async def mock_aiter_lines():
        for line in ollama_lines:
            yield line

    mock_response = MagicMock()
    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.stream.return_value = mock_stream_ctx

    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

    tokens = []
    with patch("app.rag.httpx.AsyncClient", return_value=mock_client_ctx):
        async for token in stream_answer(
            tenant_id="tenant-1",
            query="What is this about?",
            history=[],
            embeddings=mock_embeddings,
            vector_store=mock_vector_store,
            ollama_base_url="http://localhost:11434",
            model="llama3.2",
        ):
            tokens.append(token)

    assert "Hello" in tokens
    assert " world" in tokens
