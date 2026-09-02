import pytest

from backend.services.llm.base import LLMProvider, LLMError


class FakeLLM(LLMProvider):
    def __init__(self, canned_response: str):
        self._canned = canned_response

    async def complete(self, system_prompt, user_prompt, *, max_tokens=1500, temperature=0.4):
        return self._canned


@pytest.mark.asyncio
async def test_parses_clean_json():
    llm = FakeLLM('{"score": 0.8, "correct": true}')
    result = await llm.complete_json("sys", "user")
    assert result == {"score": 0.8, "correct": True}


@pytest.mark.asyncio
async def test_strips_markdown_fences():
    llm = FakeLLM('```json\n{"score": 0.5}\n```')
    result = await llm.complete_json("sys", "user")
    assert result == {"score": 0.5}


@pytest.mark.asyncio
async def test_extracts_json_from_surrounding_prose():
    llm = FakeLLM('Sure! Here is the result:\n{"score": 0.3}\nHope that helps.')
    result = await llm.complete_json("sys", "user")
    assert result == {"score": 0.3}


@pytest.mark.asyncio
async def test_raises_llm_error_on_unparseable_response():
    llm = FakeLLM("I cannot help with that.")
    with pytest.raises(LLMError):
        await llm.complete_json("sys", "user")
