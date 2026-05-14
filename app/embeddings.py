from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    def __init__(self, model_name: str, batch_size: int = 32):
        self._model = SentenceTransformer(model_name)
        self._batch_size = batch_size

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            batch_size=self._batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return [v.tolist() for v in vectors]
