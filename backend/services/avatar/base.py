import abc
from dataclasses import dataclass


@dataclass
class AvatarVideoResult:
    status: str  # "processing" | "ready" | "failed"
    video_url: str | None = None
    provider_job_id: str | None = None


class AvatarProvider(abc.ABC):
    @abc.abstractmethod
    async def generate_video(self, *, audio_url: str, script_text: str) -> AvatarVideoResult:
        """Kick off (or synchronously produce) a talking-avatar video from audio + script."""

    @abc.abstractmethod
    async def check_status(self, provider_job_id: str) -> AvatarVideoResult:
        """Poll an async provider job."""
