from __future__ import annotations
import httpx

from backend.services.avatar.base import AvatarProvider, AvatarVideoResult
from backend.core.config import get_settings


class DIDProvider(AvatarProvider):
    """Cloud talking-head video provider (d-id.com). Requires DID_API_KEY."""

    BASE_URL = "https://api.d-id.com"

    def __init__(self):
        self._settings = get_settings()

    def _auth_header(self) -> dict:
        return {"Authorization": f"Basic {self._settings.did_api_key}"}

    async def generate_video(self, *, audio_url: str, script_text: str) -> AvatarVideoResult:
        if not self._settings.did_api_key or not self._settings.did_presenter_image_url:
            raise RuntimeError(
                "DID_API_KEY / DID_PRESENTER_IMAGE_URL are not configured. Set them in .env, "
                "or switch AVATAR_PROVIDER to a self-hosted option (see docs/self_hosted_media.md). "
                "Until then, the app falls back to the in-browser 3D avatar for lip-synced audio playback."
            )
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.BASE_URL}/talks",
                headers=self._auth_header(),
                json={
                    "source_url": self._settings.did_presenter_image_url,
                    "script": {"type": "audio", "audio_url": audio_url},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return AvatarVideoResult(status="processing", provider_job_id=data["id"])

    async def check_status(self, provider_job_id: str) -> AvatarVideoResult:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{self.BASE_URL}/talks/{provider_job_id}", headers=self._auth_header())
            resp.raise_for_status()
            data = resp.json()
            status = {"done": "ready", "error": "failed"}.get(data.get("status"), "processing")
            return AvatarVideoResult(status=status, video_url=data.get("result_url"), provider_job_id=provider_job_id)
