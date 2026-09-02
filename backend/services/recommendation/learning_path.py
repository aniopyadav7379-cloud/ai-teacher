"""Learning path generation (spec section 17)."""
from __future__ import annotations
from backend.services.llm.factory import get_llm_provider
from backend.prompts.teaching import RECOMMENDATION_SYSTEM, build_learning_path_prompt


async def generate_learning_path(*, subject: str, learner_level: str, weak_concepts: list[str], goal: str) -> list[dict]:
    llm = get_llm_provider()
    prompt = build_learning_path_prompt(
        subject=subject, learner_level=learner_level,
        weak_concepts=", ".join(weak_concepts) or "none identified yet", goal=goal,
    )
    data = await llm.complete_json(RECOMMENDATION_SYSTEM, prompt, max_tokens=800, temperature=0.4)
    return data.get("path", [])
