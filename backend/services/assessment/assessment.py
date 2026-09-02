"""Final assessment + learning report generation (spec section 18)."""
from __future__ import annotations
from dataclasses import dataclass

from backend.services.llm.factory import get_llm_provider
from backend.prompts.teaching import ASSESSMENT_SYSTEM, build_assessment_prompt


@dataclass
class AssessmentReport:
    overall_score: float
    strong_areas: list[str]
    weak_areas: list[str]
    misconceptions: list[str]
    recommendation: str


async def generate_assessment(*, lesson_title: str, concept_results: list[dict], language: str) -> AssessmentReport:
    """
    concept_results: [{"concept": str, "score": float, "misconceptions": [str]}]
    """
    llm = get_llm_provider()
    summary_lines = [
        f"- {r['concept']}: score={r['score']:.2f}, misconceptions={r.get('misconceptions') or 'none'}"
        for r in concept_results
    ]
    prompt = build_assessment_prompt(
        lesson_title=lesson_title, concept_results="\n".join(summary_lines), language=language,
    )
    data = await llm.complete_json(ASSESSMENT_SYSTEM, prompt, max_tokens=700, temperature=0.3)
    return AssessmentReport(
        overall_score=float(data.get("overall_score", 0.0)),
        strong_areas=data.get("strong_areas", []),
        weak_areas=data.get("weak_areas", []),
        misconceptions=data.get("misconceptions", []),
        recommendation=data.get("recommendation", ""),
    )
