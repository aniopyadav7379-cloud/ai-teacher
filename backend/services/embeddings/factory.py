from functools import lru_cache

from backend.core.config import get_settings
from backend.services.embeddings.base import EmbeddingProvider


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "openai":
        from backend.services.embeddings.openai_provider import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider()
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider}")
