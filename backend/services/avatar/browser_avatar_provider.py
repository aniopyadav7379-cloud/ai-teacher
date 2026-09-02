"""
Zero-external-dependency fallback: no server-side video is rendered at all.
Instead the frontend's Avatar3D component (ported from 3d-teacher-ia-main,
see docs/COMPONENT_INVENTORY.md) drives lip-sync live in the browser from the
TTS audio's viseme/amplitude data. This is the DEFAULT when no avatar/video
cloud key is configured, so the product still teaches with a real speaking
avatar even with zero paid API keys.
"""
from backend.services.avatar.base import AvatarProvider, AvatarVideoResult


class BrowserAvatarProvider(AvatarProvider):
    async def generate_video(self, *, audio_url: str, script_text: str) -> AvatarVideoResult:
        # No server render needed — the browser renders live from audio_url.
        return AvatarVideoResult(status="ready", video_url=None, provider_job_id=None)

    async def check_status(self, provider_job_id: str) -> AvatarVideoResult:
        return AvatarVideoResult(status="ready")
