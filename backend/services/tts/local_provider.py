"""
Self-hosted TTS provider, backed by the RealtimeVoiceChat-main pipeline
(see docs/self_hosted_media.md for setup — requires a CUDA GPU host).

This is intentionally a documented stub, not a fake implementation: wiring it
requires the RealtimeVoiceChat server (code/audio_module.py, RealtimeTTS) to
be running as a sidecar service. Once that's deployed, implement `synthesize`
below to call its REST/WebSocket endpoint and return real audio bytes.
"""
from backend.services.tts.base import TTSProvider, TTSResult


class LocalRealtimeVoiceChatProvider(TTSProvider):
    def __init__(self, endpoint: str | None = None):
        from backend.core.config import get_settings
        self._endpoint = endpoint or get_settings().local_tts_endpoint

    async def synthesize(self, text: str, *, language: str = "en", voice_id: str | None = None) -> TTSResult:
        raise NotImplementedError(
            "Local TTS requires a running RealtimeVoiceChat sidecar (GPU host). "
            "See docs/self_hosted_media.md to enable this provider."
        )
