from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.security import get_current_user
from backend import models
from backend.schemas.schemas import StudentProfileOut, LearnerProfileIn

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/profile", response_model=StudentProfileOut)
def get_profile(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    profile = db.query(models.StudentProfile).filter_by(user_id=user.id).first()
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile


@router.put("/profile", response_model=StudentProfileOut)
def update_profile(payload: LearnerProfileIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    profile = db.query(models.StudentProfile).filter_by(user_id=user.id).first()
    if profile is None:
        raise HTTPException(404, "Profile not found")
    profile.education_level = payload.learner_level
    profile.preferred_language = payload.language
    profile.preferred_teaching_style = payload.teaching_style
    profile.default_depth = payload.depth
    db.commit()
    db.refresh(profile)
    return profile
