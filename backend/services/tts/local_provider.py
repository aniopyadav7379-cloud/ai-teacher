"""
Local TTS provider backed by the Kokoro FastAPI sidecar.

The sidecar runs separately on the GPU machine, typically at:
    http://127.0.0.1:8001

It accepts JSON at POST /synthesize and returns audio/wav bytes.
"""

from __future__ import annotations

import httpx

from backend.services.tts.base import TTSProvider, TTSResult


class LocalRealtimeVoiceChatProvider(TTSProvider):
    def __init__(self, endpoint: str | None = None):
        from backend.core.config import get_settings

        self._endpoint = (
            endpoint or get_settings().local_tts_endpoint
        ).rstrip("/")

    async def synthesize(
        self,
        text: str,
        *,
        language: str = "en",
        voice_id: str | None = None,
    ) -> TTSResult:
        text = text.strip()

        if not text:
            raise ValueError("TTS text cannot be empty")

        payload = {
            "text": text,
            "language": language,
            "voice_id": voice_id or "af_heart",
            "speed": 1.0,
        }

        url = f"{self._endpoint}/synthesize"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                )

            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Local TTS returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:500]}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Could not connect to local TTS sidecar at {url}: {exc}"
            ) from exc

        audio_bytes = response.content

        if not audio_bytes:
            raise RuntimeError("Local TTS returned empty audio")

        return TTSResult(
            audio_bytes=audio_bytes,
            content_type=response.headers.get(
                "content-type",
                "audio/wav",
            ).split(";")[0],
            duration_seconds=None,
            visemes=None,
        )