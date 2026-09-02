from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.security import get_current_user
from backend import models
from backend.schemas.schemas import LessonOut
from backend.services.lesson.planner import plan_lesson
from backend.services.lesson.translator import switch_lesson_language

router = APIRouter(prefix="/api", tags=["lessons"])


@router.post("/sessions/{session_id}/plan", response_model=LessonOut, status_code=201)
async def create_lesson_plan(session_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    session = db.get(models.LearningSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "Session not found")

    session.status = "planning"
    db.commit()

    material_ids = []
    if session.mode == "material":
        materials = db.query(models.UploadedMaterial).filter_by(session_id=session_id, status="ready").all()
        if not materials:
            raise HTTPException(
                409,
                "No processed materials are ready yet for this session. "
                "Upload a document and wait for status='ready' before planning.",
            )
        material_ids = [m.id for m in materials]

    try:
        plan = await plan_lesson(
            topic=session.topic,
            material_ids=material_ids,
            learner_level=session.learner_level,
            goal=session.goal,
            language=session.language,
            teaching_style=session.teaching_style,
            available_minutes=session.available_minutes,
            depth=session.depth,
        )
    except Exception as e:
        session.status = "error"
        db.commit()
        raise HTTPException(502, f"Lesson planning failed: {e}") from e

    lesson = models.Lesson(
        session_id=session_id,
        title=plan.lesson_title,
        learner_level=session.learner_level,
        language=session.language,
        duration_minutes=session.available_minutes,
        learning_objectives=plan.learning_objectives,
        grounded_in_material=plan.grounded_in_material,
        status="planned",
    )
    db.add(lesson)
    db.flush()

    for i, c in enumerate(plan.concepts):
        concept = models.LessonConcept(
            lesson_id=lesson.id,
            order_index=i,
            concept=c.concept,
            importance=c.importance,
            estimated_minutes=c.estimated_minutes,
            explanation_depth=c.explanation_depth,
            prerequisite=c.prerequisite,
            explanation=c.explanation,
            example=c.example,
            analogy=c.analogy,
            source_citation=c.source_citation,
            visual_spec={"visual_type": c.visual_type},
            status="pending",
        )
        db.add(concept)
        db.flush()
        db.add(
            models.Question(
                concept_id=concept.id,
                question_type=c.question.question_type,
                prompt=c.question.prompt,
                options=c.question.options,
                correct_answer=c.question.correct_answer,
                difficulty=c.question.difficulty,
            )
        )

    session.status = "ready"
    db.commit()
    db.refresh(lesson)
    return lesson


@router.post("/sessions/{session_id}/start")
def start_lesson(session_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    session = db.get(models.LearningSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "Session not found")
    lesson = db.query(models.Lesson).filter_by(session_id=session_id).order_by(models.Lesson.created_at.desc()).first()
    if lesson is None:
        raise HTTPException(404, "No lesson plan exists yet — call /plan first.")
    lesson.status = "in_progress"
    session.status = "teaching"
    db.commit()
    return {"lesson_id": lesson.id, "status": lesson.status}


@router.get("/lessons/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    lesson = db.get(models.Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(404, "Lesson not found")
    out = LessonOut.model_validate(lesson)
    for i, c in enumerate(lesson.concepts):
        if c.questions:
            out.concepts[i].question = c.questions[0]
    return out


class LanguageSwitchIn(BaseModel):
    language: str


@router.post("/lessons/{lesson_id}/language", response_model=LessonOut)
async def switch_language(
    lesson_id: str, payload: LanguageSwitchIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    """
    Switches the language of an in-progress lesson WITHOUT resetting it.
    Translates only the not-yet-taught concepts (and the active question) in
    place; current_concept_index, mastery status, and response history are
    untouched — see backend/services/lesson/translator.py for why this is
    safe (lesson state is keyed by concept ID, not by rendered text).
    """
    lesson = db.get(models.Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(404, "Lesson not found")
    session = db.get(models.LearningSession, lesson.session_id)
    if session.user_id != user.id:
        raise HTTPException(403, "Not your session")

    try:
        lesson = await switch_lesson_language(db, lesson, payload.language)
    except Exception as e:
        raise HTTPException(502, f"Language switch failed: {e}") from e

    out = LessonOut.model_validate(lesson)
    for i, c in enumerate(lesson.concepts):
        if c.questions:
            out.concepts[i].question = c.questions[0]
    return out
