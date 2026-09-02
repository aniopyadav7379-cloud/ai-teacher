"""
Executes the REEXPLAIN_* adaptation actions: generates a genuinely different
explanation/analogy/example plus a targeted follow-up question.
"""
from __future__ import annotations
from dataclasses import dataclass

from backend.services.llm.factory import get_llm_provider
from backend.prompts.teaching import REEXPLAIN_SYSTEM, build_reexplain_prompt


@dataclass
class ReexplanationResult:
    reexplanation: str
    new_analogy: str
    new_example: str
    followup_question: dict


async def generate_reexplanation(
    *,
    concept: str,
    original_explanation: str,
    original_analogy: str,
    misconception: str,
    learner_level: str,
    language: str,
) -> ReexplanationResult:
    llm = get_llm_provider()
    prompt = build_reexplain_prompt(
        concept=concept,
        original_explanation=original_explanation,
        original_analogy=original_analogy,
        misconception=misconception or "General difficulty grasping the concept.",
        learner_level=learner_level,
        language=language,
    )
    data = await llm.complete_json(REEXPLAIN_SYSTEM, prompt, max_tokens=900, temperature=0.5)
    return ReexplanationResult(
        reexplanation=data.get("reexplanation", ""),
        new_analogy=data.get("new_analogy", ""),
        new_example=data.get("new_example", ""),
        followup_question=data.get("followup_question", {}),
    )
