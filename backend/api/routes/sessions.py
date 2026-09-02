from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.security import get_current_user
from backend import models
from backend.schemas.schemas import SessionCreate, SessionOut

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if payload.mode not in ("material", "topic"):
        raise HTTPException(400, "mode must be 'material' or 'topic'")
    if payload.mode == "topic" and not payload.topic:
        raise HTTPException(400, "topic is required when mode='topic'")

    session = models.LearningSession(
        user_id=user.id,
        mode=payload.mode,
        topic=payload.topic,
        learner_level=payload.profile.learner_level,
        goal=payload.profile.goal,
        language=payload.profile.language,
        teaching_style=payload.profile.teaching_style,
        available_minutes=payload.profile.available_minutes,
        depth=payload.profile.depth,
        status="created",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    session = db.get(models.LearningSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "Session not found")
    return session
