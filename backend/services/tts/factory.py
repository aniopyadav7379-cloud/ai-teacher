from functools import lru_cache

from backend.core.config import get_settings
from backend.services.tts.base import TTSProvider


@lru_cache
def get_tts_provider() -> TTSProvider:
    settings = get_settings()
    if settings.tts_provider == "elevenlabs":
        from backend.services.tts.elevenlabs_provider import ElevenLabsProvider
        return ElevenLabsProvider()
    if settings.tts_provider == "local_realtimevoicechat":
        from backend.services.tts.local_provider import LocalRealtimeVoiceChatProvider
        return LocalRealtimeVoiceChatProvider()
    raise ValueError(f"Unknown TTS_PROVIDER: {settings.tts_provider}")
