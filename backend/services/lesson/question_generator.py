"""Question generation (spec section 11) for on-demand extra questions
(e.g. the adaptive engine's ADVANCE_INCREASE_DIFFICULTY path)."""
from __future__ import annotations
from backend.services.llm.factory import get_llm_provider
from backend.prompts.teaching import QUESTION_GEN_SYSTEM, build_question_prompt


async def generate_question(*, concept: str, learner_level: str, difficulty: str, question_type: str, language: str) -> dict:
    llm = get_llm_provider()
    prompt = build_question_prompt(
        concept=concept, learner_level=learner_level, difficulty=difficulty,
        question_type=question_type, language=language,
    )
    return await llm.complete_json(QUESTION_GEN_SYSTEM, prompt, max_tokens=400, temperature=0.5)
