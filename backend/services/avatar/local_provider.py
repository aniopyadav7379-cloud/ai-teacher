"""
Self-hosted talking-head provider backed by Linly-Talker-main (SadTalker /
Wav2Lip). See docs/self_hosted_media.md — requires a CUDA GPU host and the
Linly-Talker submodules/model weights to be present.
"""
from backend.services.avatar.base import AvatarProvider, AvatarVideoResult


class LocalLinlyTalkerProvider(AvatarProvider):
    def __init__(self, endpoint: str | None = None):
        from backend.core.config import get_settings
        self._endpoint = endpoint or get_settings().local_avatar_endpoint

    async def generate_video(self, *, audio_url: str, script_text: str) -> AvatarVideoResult:
        raise NotImplementedError(
            "Local avatar generation requires a running Linly-Talker sidecar (GPU host). "
            "See docs/self_hosted_media.md to enable this provider."
        )

    async def check_status(self, provider_job_id: str) -> AvatarVideoResult:
        raise NotImplementedError("See generate_video.")
