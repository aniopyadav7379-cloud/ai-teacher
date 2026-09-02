from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.security import get_current_user
from backend import models
from backend.schemas.schemas import AnswerIn, AnswerResponseOut, EvaluationOut, ConceptOut
from backend.agents.teacher_agent import process_student_answer

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.post("/{question_id}/answer", response_model=AnswerResponseOut)
async def answer_question(
    question_id: str, payload: AnswerIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    question = db.get(models.Question, question_id)
    if question is None:
        raise HTTPException(404, "Question not found")
    concept = db.get(models.LessonConcept, question.concept_id)
    lesson = db.get(models.Lesson, concept.lesson_id)
    session = db.get(models.LearningSession, lesson.session_id)
    if session.user_id != user.id:
        raise HTTPException(403, "Not your session")

    try:
        outcome = await process_student_answer(
            db,
            question=question,
            concept=concept,
            lesson=lesson,
            answer_text=payload.answer_text,
            language=lesson.language,
            learner_level=lesson.learner_level,
        )
    except Exception as e:
        raise HTTPException(502, f"Evaluation failed: {e}") from e

    # update learner profile mastery signal
    profile = db.query(models.StudentProfile).filter_by(user_id=user.id).first()
    if profile:
        if outcome.evaluation.score >= 0.85 and concept.concept not in profile.strong_concepts:
            profile.strong_concepts = [*profile.strong_concepts, concept.concept]
        if outcome.evaluation.classification == "incorrect" and concept.concept not in profile.weak_concepts:
            profile.weak_concepts = [*profile.weak_concepts, concept.concept]
        db.commit()

    db.refresh(lesson)
    next_concept = None
    if outcome.advanced and lesson.concepts:
        nc = lesson.concepts[lesson.current_concept_index]
        next_concept = ConceptOut.model_validate(nc)
        if nc.questions:
            next_concept.question = nc.questions[0]

    return AnswerResponseOut(
        evaluation=EvaluationOut(
            correct=outcome.evaluation.correct,
            classification=outcome.evaluation.classification,
            score=outcome.evaluation.score,
            misconception=outcome.evaluation.misconception,
            severity=outcome.evaluation.severity,
            reasoning=outcome.evaluation.reasoning,
        ),
        action=outcome.action.value,
        action_reason=outcome.action_reason,
        reexplanation=outcome.reexplanation,
        advanced=outcome.advanced,
        lesson_status=lesson.status,
        next_concept=next_concept,
    )
