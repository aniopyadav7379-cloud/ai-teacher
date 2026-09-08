from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.services.llm.base import LLMProvider, LLMError
from backend.core.config import get_settings


class OllamaProvider(LLMProvider):
    """Local Ollama LLM provider."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        settings = get_settings()

        self._base_url = (
            base_url or settings.ollama_base_url
        ).rstrip("/")

        self._model = model or settings.ollama_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(
            (httpx.ConnectError, httpx.TimeoutException)
        ),
        reraise=True,
    )
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 1500,
        temperature: float = 0.4,
    ) -> str:
        payload = {
            "model": self._model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.HTTPError as exc:
            raise LLMError(
                f"Ollama connection/API error: {exc}"
            ) from exc

        data = response.json()

        text = data.get("response", "")

        if not text:
            raise LLMError(
                "Ollama returned an empty response."
            )

        return text