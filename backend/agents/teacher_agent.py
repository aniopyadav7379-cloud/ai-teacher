"""
AI TEACHER AGENT (spec section 9).

The orchestrator's job is to answer "what should I teach next?", not just
"what answer should I give?". It holds no long-lived in-memory state itself
(this is a stateless HTTP API) — instead it reconstructs the teaching
context from the DB on every call, which makes it safe to run multiple
backend workers and survive restarts mid-lesson.
"""
from __future__ import annotations
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend import models
from backend.services.evaluation.evaluator import evaluate_answer, EvaluationResult
from backend.services.adaptation.engine import decide_next_action, AdaptationAction
from backend.services.adaptation.reteach import generate_reexplanation


@dataclass
class TeachingContext:
    session: models.LearningSession
    lesson: models.Lesson
    concept: models.LessonConcept
    consecutive_struggles: int


def get_teaching_context(db: Session, lesson_id: str) -> TeachingContext:
    lesson = db.get(models.Lesson, lesson_id)
    if lesson is None:
        raise ValueError("Lesson not found")
    session = db.get(models.LearningSession, lesson.session_id)
    idx = min(lesson.current_concept_index, max(len(lesson.concepts) - 1, 0))
    concept = lesson.concepts[idx] if lesson.concepts else None
    if concept is None:
        raise ValueError("Lesson has no concepts")

    # Count consecutive incorrect responses on the CURRENT concept only.
    struggles = 0
    for q in sorted(concept.questions, key=lambda q: q.created_at, reverse=True):
        for r in sorted(q.responses, key=lambda r: r.created_at, reverse=True):
            if r.classification == "incorrect":
                struggles += 1
            else:
                break
            break  # only look at the latest response per question
    return TeachingContext(session=session, lesson=lesson, concept=concept, consecutive_struggles=struggles)


@dataclass
class AnswerOutcome:
    evaluation: EvaluationResult
    action: AdaptationAction
    action_reason: str
    reexplanation: dict | None
    advanced: bool


async def process_student_answer(
    db: Session,
    *,
    question: models.Question,
    concept: models.LessonConcept,
    lesson: models.Lesson,
    answer_text: str,
    language: str,
    learner_level: str,
) -> AnswerOutcome:
    """
    The core UNDERSTAND->EVALUATE->ADAPT step of the teaching loop
    (spec section 2). Persists the response + evaluation, decides the next
    pedagogical action, and — if the action calls for it — generates the
    re-explanation content immediately so the frontend gets one response.
    """
    evaluation = await evaluate_answer(
        concept=concept.concept,
        question_prompt=question.prompt,
        correct_answer=question.correct_answer,
        student_answer=answer_text,
        language=language,
    )

    response = models.StudentResponse(
        question_id=question.id,
        answer_text=answer_text,
        correct=evaluation.correct,
        score=evaluation.score,
        classification=evaluation.classification,
        misconception=evaluation.misconception,
        severity=evaluation.severity,
        recommended_action=evaluation.recommended_action,
        evaluator_reasoning=evaluation.reasoning,
    )
    db.add(response)

    # Count prior consecutive struggles BEFORE this answer for the decision engine.
    ctx = get_teaching_context(db, lesson.id)
    decision = decide_next_action(evaluation, consecutive_struggles=ctx.consecutive_struggles)

    reexplanation = None
    advanced = False

    if decision.action in (AdaptationAction.REEXPLAIN_NEW_ANALOGY, AdaptationAction.REEXPLAIN_SIMPLER):
        result = await generate_reexplanation(
            concept=concept.concept,
            original_explanation=concept.explanation,
            original_analogy=concept.analogy,
            misconception=evaluation.misconception or "",
            learner_level=learner_level,
            language=language,
        )
        reexplanation = {
            "reexplanation": result.reexplanation,
            "new_analogy": result.new_analogy,
            "new_example": result.new_example,
            "followup_question": result.followup_question,
        }
        concept.status = "struggling"

    elif decision.action == AdaptationAction.CLARIFY_GAP:
        concept.status = "struggling"

    elif decision.action in (AdaptationAction.ADVANCE, AdaptationAction.ADVANCE_INCREASE_DIFFICULTY):
        concept.status = "mastered" if evaluation.score >= 0.85 else "taught"
        advanced = _advance_lesson(lesson)

    elif decision.action == AdaptationAction.REINFORCE:
        concept.status = "taught"

    db.commit()

    return AnswerOutcome(
        evaluation=evaluation,
        action=decision.action,
        action_reason=decision.reason,
        reexplanation=reexplanation,
        advanced=advanced,
    )


def _advance_lesson(lesson: models.Lesson) -> bool:
    """Moves to the next concept if one exists. Returns True if it advanced."""
    if lesson.current_concept_index < len(lesson.concepts) - 1:
        lesson.current_concept_index += 1
        return True
    lesson.status = "completed"
    return False
