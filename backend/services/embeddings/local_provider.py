from __future__ import annotations

import asyncio

from sentence_transformers import SentenceTransformer

from backend.services.embeddings.base import EmbeddingProvider
from backend.core.config import get_settings


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformers embedding provider."""

    def __init__(self):
        settings = get_settings()

        self._model = SentenceTransformer(
            settings.embedding_model
        )

    async def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return await asyncio.to_thread(
            self._encode,
            texts,
        )

    async def embed_query(
        self,
        text: str,
    ) -> list[float]:
        result = await self.embed([text])
        return result[0]

    def _encode(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings.tolist()