import abc
from dataclasses import dataclass


@dataclass
class TTSResult:
    audio_bytes: bytes
    content_type: str  # e.g. "audio/mpeg"
    duration_seconds: float | None = None
    visemes: list[dict] | None = None  # [{time, viseme}] if provider supports it


class TTSProvider(abc.ABC):
    @abc.abstractmethod
    async def synthesize(self, text: str, *, language: str = "en", voice_id: str | None = None) -> TTSResult:
        """Convert text into speech audio."""
