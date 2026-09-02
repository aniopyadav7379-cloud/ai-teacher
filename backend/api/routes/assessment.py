from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.security import get_current_user
from backend import models
from backend.schemas.schemas import AssessmentOut
from backend.services.assessment.assessment import generate_assessment

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.post("/generate/{lesson_id}", response_model=AssessmentOut)
async def generate(lesson_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    lesson = db.get(models.Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(404, "Lesson not found")

    concept_results = []
    for c in lesson.concepts:
        latest_scores = [r.score for q in c.questions for r in q.responses]
        misconceptions = [r.misconception for q in c.questions for r in q.responses if r.misconception]
        concept_results.append(
            {"concept": c.concept, "score": max(latest_scores) if latest_scores else 0.0, "misconceptions": misconceptions}
        )

    try:
        report = await generate_assessment(lesson_title=lesson.title, concept_results=concept_results, language=lesson.language)
    except Exception as e:
        raise HTTPException(502, f"Assessment generation failed: {e}") from e

    assessment = models.Assessment(
        lesson_id=lesson_id,
        overall_score=report.overall_score,
        strong_areas=report.strong_areas,
        weak_areas=report.weak_areas,
        misconceptions=report.misconceptions,
        recommendation=report.recommendation,
    )
    db.add(assessment)
    db.flush()
    for cr in concept_results:
        db.add(models.AssessmentResult(assessment_id=assessment.id, concept=cr["concept"], score=cr["score"], mastered=cr["score"] >= 0.85))

    profile = db.query(models.StudentProfile).filter_by(user_id=user.id).first()
    if profile:
        profile.weak_concepts = list({*profile.weak_concepts, *report.weak_areas})
        profile.strong_concepts = list({*profile.strong_concepts, *report.strong_areas} - set(report.weak_areas))
        if lesson.title not in profile.topics_studied:
            profile.topics_studied = [*profile.topics_studied, lesson.title]

    lesson.status = "completed"
    db.commit()

    return AssessmentOut(
        overall_score=report.overall_score,
        strong_areas=report.strong_areas,
        weak_areas=report.weak_areas,
        misconceptions=report.misconceptions,
        recommendation=report.recommendation,
    )


@router.get("/{lesson_id}", response_model=AssessmentOut)
def get_assessment(lesson_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    lesson = db.get(models.Lesson, lesson_id)
    if lesson is None or lesson.assessment is None:
        raise HTTPException(404, "No assessment generated yet for this lesson.")
    a = lesson.assessment
    return AssessmentOut(
        overall_score=a.overall_score, strong_areas=a.strong_areas, weak_areas=a.weak_areas,
        misconceptions=a.misconceptions, recommendation=a.recommendation,
    )
