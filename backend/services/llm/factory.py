from functools import lru_cache

from backend.core.config import get_settings
from backend.services.llm.base import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        from backend.services.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")
