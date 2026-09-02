from __future__ import annotations
import httpx

from backend.services.tts.base import TTSProvider, TTSResult
from backend.core.config import get_settings


class ElevenLabsProvider(TTSProvider):
    """Cloud TTS — default provider. Requires ELEVENLABS_API_KEY."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self):
        self._settings = get_settings()

    def _voice_for_language(self, language: str, override: str | None) -> str:
        if override:
            return override
        if language.startswith("hi") and self._settings.elevenlabs_voice_id_hi:
            return self._settings.elevenlabs_voice_id_hi
        return self._settings.elevenlabs_voice_id_en

    async def synthesize(self, text: str, *, language: str = "en", voice_id: str | None = None) -> TTSResult:
        if not self._settings.elevenlabs_api_key:
            raise RuntimeError(
                "ELEVENLABS_API_KEY is not configured. Set it in .env, or switch "
                "TTS_PROVIDER to a self-hosted option (see docs/self_hosted_media.md)."
            )
        voice = self._voice_for_language(language, voice_id)
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.BASE_URL}/text-to-speech/{voice}",
                headers={
                    "xi-api-key": self._settings.elevenlabs_api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
            )
            resp.raise_for_status()
            return TTSResult(audio_bytes=resp.content, content_type="audio/mpeg")
