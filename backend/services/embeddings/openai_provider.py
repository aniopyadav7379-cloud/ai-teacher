from __future__ import annotations
import httpx

from backend.services.embeddings.base import EmbeddingProvider
from backend.core.config import get_settings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Calls OpenAI's /v1/embeddings REST endpoint directly (no extra SDK dependency)."""

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.openai_api_key
        self._model = settings.embedding_model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Set it in .env — required for "
                "document embeddings used by the RAG pipeline."
            )
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in sorted(data["data"], key=lambda d: d["index"])]

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed([text]))[0]
