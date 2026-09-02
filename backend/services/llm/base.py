"""
LLMProvider interface. All teaching intelligence (planning, evaluation,
adaptation, question generation) calls the LLM only through this interface,
so swapping providers never touches business logic.
"""
from __future__ import annotations
import abc
import json
from typing import Any


class LLMError(Exception):
    """Raised on provider failure after retries are exhausted."""


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 1500,
        temperature: float = 0.4,
    ) -> str:
        """Return raw text completion."""

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 1500,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """
        Return parsed structured JSON. Appends a strict JSON-only instruction
        and repairs common formatting issues (fenced code blocks) before parsing.
        Raises LLMError with the raw text attached if parsing still fails.
        """
        strict_system = (
            system_prompt
            + "\n\nCRITICAL: Respond with ONLY a single valid JSON object. "
              "No markdown fences, no commentary, no preamble or explanation."
        )
        raw = await self.complete(strict_system, user_prompt, max_tokens=max_tokens, temperature=temperature)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # last-resort: try to find the outermost {...}
            start, end = cleaned.find("{"), cleaned.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(cleaned[start : end + 1])
                except json.JSONDecodeError:
                    pass
            raise LLMError(f"Model did not return valid JSON: {e}\nRaw: {raw[:500]}") from e
