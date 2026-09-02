import abc


class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""

    @abc.abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
