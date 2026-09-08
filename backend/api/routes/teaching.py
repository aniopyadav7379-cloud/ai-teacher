"""Media pipeline endpoints (spec section 14) + visual planning (section 13)."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.security import get_current_user
from backend import models
from backend.schemas.schemas import TeachingVideoOut
from backend.services.video.pipeline import generate_teaching_video, poll_avatar_status
from backend.services.visual.planner import plan_visual
from backend.jobs.queue import get_job_queue

router = APIRouter(prefix="/api/teaching", tags=["teaching"])


@router.post("/video/{concept_id}/generate", status_code=202)
def kick_off_video(
    concept_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    concept = db.get(models.LessonConcept, concept_id)

    if concept is None:
        raise HTTPException(404, "Concept not found")

    # Create the video row BEFORE enqueueing the background job.
    # This makes the operation safe even if the frontend sends
    # multiple generate requests at nearly the same time.
    if concept.video is None:
        video = models.TeachingVideo(
            concept_id=concept_id,
            status="queued",
        )
        db.add(video)

        try:
            db.commit()
            db.refresh(video)
        except Exception:
            db.rollback()

            # Another concurrent request may have created it.
            concept = db.get(models.LessonConcept, concept_id)

            if concept.video is not None:
                return {
                    "status": "already_started",
                    "video_status": concept.video.status,
                }

            raise

    else:
        return {
            "status": "already_started",
            "video_status": concept.video.status,
        }

    lesson = db.get(models.Lesson, concept.lesson_id)

    if lesson is None:
        raise HTTPException(404, "Lesson not found")

    get_job_queue(background_tasks).enqueue(
        _run_video_gen,
        concept_id,
        lesson.language,
    )

    return {"status": "started"}

def _run_video_gen(concept_id: str, language: str):
    import asyncio
    from backend.database.session import SessionLocal
    db = SessionLocal()
    try:
        asyncio.run(generate_teaching_video(db, concept_id, language))
    finally:
        db.close()


@router.get("/video/{concept_id}", response_model=TeachingVideoOut)
async def get_video_status(concept_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    concept = db.get(models.LessonConcept, concept_id)
    if concept is None:
        raise HTTPException(404, "Concept not found")
    video = await poll_avatar_status(db, concept_id) if concept.video else None
    if video is None:
        raise HTTPException(404, "Video generation has not been started for this concept.")
    return video


@router.get("/visual/{concept_id}")
async def get_visual(concept_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    concept = db.get(models.LessonConcept, concept_id)
    if concept is None:
        raise HTTPException(404, "Concept not found")
    lesson = db.get(models.Lesson, concept.lesson_id)
    try:
        spec = await plan_visual(subject=lesson.title, concept=concept.concept, explanation=concept.explanation)
    except Exception as e:
        raise HTTPException(502, f"Visual planning failed: {e}") from e
    return spec