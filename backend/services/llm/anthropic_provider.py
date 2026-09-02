from __future__ import annotations
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.services.llm.base import LLMProvider, LLMError
from backend.core.config import get_settings


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self._api_key = api_key or settings.anthropic_api_key
        self._model = model or settings.anthropic_model
        if not self._api_key:
            # Deliberately not raising here: allows the app to boot and show a
            # clear, actionable error only when a teaching call is actually made.
            self._client = None
        else:
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.APIStatusError)),
        reraise=True,
    )
    async def complete(self, system_prompt: str, user_prompt: str, *, max_tokens: int = 1500, temperature: float = 0.4) -> str:
        if self._client is None:
            raise LLMError(
                "ANTHROPIC_API_KEY is not configured. Set it in your .env file — "
                "see .env.example. No teaching content can be generated without an LLM key."
            )
        try:
            resp = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as e:
            raise LLMError(f"Anthropic API error: {e}") from e

        return "".join(block.text for block in resp.content if block.type == "text")
