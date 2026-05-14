from unittest.mock import patch, MagicMock
import numpy as np
from app.embeddings import EmbeddingService


def test_embed_batch_returns_list_of_vectors():
    with patch("app.embeddings.SentenceTransformer") as MockST:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1] * 768, [0.2] * 768])
        MockST.return_value = mock_model

        service = EmbeddingService("BAAI/bge-base-en-v1.5")
        result = service.embed_batch(["text one", "text two"])

        assert len(result) == 2
        assert len(result[0]) == 768
        assert isinstance(result[0][0], float)


def test_embed_batch_calls_encode_with_correct_batch_size():
    with patch("app.embeddings.SentenceTransformer") as MockST:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1] * 768])
        MockST.return_value = mock_model

        service = EmbeddingService("BAAI/bge-base-en-v1.5", batch_size=16)
        service.embed_batch(["hello"])

        mock_model.encode.assert_called_once_with(
            ["hello"],
            batch_size=16,
            show_progress_bar=False,
            normalize_embeddings=True,
        )


def test_embed_batch_empty_list_returns_empty():
    with patch("app.embeddings.SentenceTransformer") as MockST:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([]).reshape(0, 768)
        MockST.return_value = mock_model

        service = EmbeddingService("BAAI/bge-base-en-v1.5")
        result = service.embed_batch([])

        assert result == []
