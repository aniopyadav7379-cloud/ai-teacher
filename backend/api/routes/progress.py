from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.security import get_current_user
from backend import models

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/progress")
def get_progress(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    sessions = db.query(models.LearningSession).filter_by(user_id=user.id).all()
    lessons = [l for s in sessions for l in s.lessons]
    completed = [l for l in lessons if l.status == "completed"]
    profile = db.query(models.StudentProfile).filter_by(user_id=user.id).first()
    return {
        "total_sessions": len(sessions),
        "total_lessons": len(lessons),
        "completed_lessons": len(completed),
        "topics_studied": profile.topics_studied if profile else [],
        "strong_concepts": profile.strong_concepts if profile else [],
        "weak_concepts": profile.weak_concepts if profile else [],
        "history": [
            {"lesson_id": l.id, "title": l.title, "status": l.status, "created_at": l.created_at.isoformat()}
            for l in sorted(lessons, key=lambda l: l.created_at, reverse=True)
        ],
    }
