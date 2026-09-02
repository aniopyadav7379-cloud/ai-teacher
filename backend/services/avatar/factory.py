from functools import lru_cache

from backend.core.config import get_settings
from backend.services.avatar.base import AvatarProvider


@lru_cache
def get_avatar_provider() -> AvatarProvider:
    settings = get_settings()
    if settings.avatar_provider == "did":
        if not settings.did_api_key:
            from backend.services.avatar.browser_avatar_provider import BrowserAvatarProvider
            return BrowserAvatarProvider()
        from backend.services.avatar.did_provider import DIDProvider
        return DIDProvider()
    if settings.avatar_provider == "browser":
        from backend.services.avatar.browser_avatar_provider import BrowserAvatarProvider
        return BrowserAvatarProvider()
    if settings.avatar_provider == "local_linlytalker":
        from backend.services.avatar.local_provider import LocalLinlyTalkerProvider
        return LocalLinlyTalkerProvider()
    raise ValueError(f"Unknown AVATAR_PROVIDER: {settings.avatar_provider}")
