from pathlib import Path
from urllib.parse import urlparse

import httpx

from backend.core.config import get_settings
from backend.services.avatar.base import AvatarProvider, AvatarVideoResult


class LocalLinlyTalkerProvider(AvatarProvider):
    def __init__(self, endpoint: str | None = None):
        settings = get_settings()
        self._endpoint = (
            endpoint or settings.local_avatar_endpoint
        ).rstrip("/")
        self._media_dir = Path(settings.media_dir)

    def _resolve_audio_path(self, audio_url: str) -> Path:
        """
        Convert an AI Teacher media URL such as:
            /media/<uuid>.wav

        into the actual local media file.
        """
        parsed = urlparse(audio_url)
        path = parsed.path
        filename = Path(path).name

        if not filename:
            raise ValueError(f"Invalid audio URL: {audio_url}")

        audio_path = self._media_dir / filename

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        return audio_path

    async def generate_video(
        self,
        *,
        audio_url: str,
        script_text: str,
    ) -> AvatarVideoResult:
        audio_path = self._resolve_audio_path(audio_url)

        timeout = httpx.Timeout(
            connect=30.0,
            read=600.0,
            write=60.0,
            pool=30.0,
        )

        try:
            async with httpx.AsyncClient(
                timeout=timeout
            ) as client:
                with audio_path.open("rb") as audio_file:
                    files = {
                        "audio": (
                            audio_path.name,
                            audio_file,
                            "audio/wav",
                        )
                    }

                    data = {
                        "script_text": script_text or "",
                    }

                    response = await client.post(
                        f"{self._endpoint}/generate",
                        files=files,
                        data=data,
                    )

                response.raise_for_status()
                payload = response.json()

        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:1000]
            raise RuntimeError(
                f"Linly-Talker returned HTTP "
                f"{exc.response.status_code}: {detail}"
            ) from exc

        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Could not connect to Linly-Talker at "
                f"{self._endpoint}: {exc}"
            ) from exc

        status = payload.get("status")

        if status != "ready":
            raise RuntimeError(
                f"Linly-Talker did not return a ready video: "
                f"{payload}"
            )

        video_url = payload.get("video_url")

        if video_url and video_url.startswith("/"):
            video_url = f"{self._endpoint}{video_url}"

        if not video_url:
            raise RuntimeError(
                f"Linly-Talker response has no video_url: "
                f"{payload}"
            )

        return AvatarVideoResult(
            status="ready",
            video_url=video_url,
            provider_job_id=payload.get("provider_job_id"),
        )

    async def check_status(
        self,
        provider_job_id: str,
    ) -> AvatarVideoResult:
        # Current Linly-Talker sidecar performs generation
        # synchronously, so there is no separate polling job.
        return AvatarVideoResult(
            status="ready",
            provider_job_id=provider_job_id,
        )