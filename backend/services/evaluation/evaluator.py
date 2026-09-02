"""
Answer evaluation + misconception detection (spec sections 11-12).
Returns structured diagnostic data — never just "right/wrong".
"""
from __future__ import annotations
from dataclasses import dataclass

from backend.services.llm.factory import get_llm_provider
from backend.prompts.evaluation import EVALUATOR_SYSTEM, build_evaluation_prompt


@dataclass
class EvaluationResult:
    correct: bool
    classification: str  # correct|partially_correct|incorrect|uncertain
    score: float
    misconception: str | None
    misconception_type: str | None
    severity: str | None
    reasoning: str
    recommended_action: str


async def evaluate_answer(
    *,
    concept: str,
    question_prompt: str,
    correct_answer: str,
    student_answer: str,
    language: str = "en",
) -> EvaluationResult:
    llm = get_llm_provider()
    prompt = build_evaluation_prompt(
        concept=concept,
        question_prompt=question_prompt,
        correct_answer=correct_answer,
        student_answer=student_answer,
        language=language,
    )
    data = await llm.complete_json(EVALUATOR_SYSTEM, prompt, max_tokens=600, temperature=0.1)

    return EvaluationResult(
        correct=bool(data.get("correct", False)),
        classification=data.get("classification", "uncertain"),
        score=float(data.get("score", 0.0)),
        misconception=data.get("misconception"),
        misconception_type=data.get("misconception_type"),
        severity=data.get("severity"),
        reasoning=data.get("reasoning", ""),
        recommended_action=data.get("recommended_action", "clarify_gap"),
    )
