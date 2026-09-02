from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.security import get_current_user
from backend import models
from backend.schemas.schemas import LearningPathOut
from backend.services.recommendation.learning_path import generate_learning_path

router = APIRouter(prefix="/api/learning-path", tags=["learning-path"])


@router.post("", response_model=LearningPathOut, status_code=201)
async def create_learning_path(subject: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    profile = db.query(models.StudentProfile).filter_by(user_id=user.id).first()
    if profile is None:
        raise HTTPException(404, "Profile not found")

    try:
        nodes_data = await generate_learning_path(
            subject=subject, learner_level=profile.education_level,
            weak_concepts=profile.weak_concepts, goal=subject,
        )
    except Exception as e:
        raise HTTPException(502, f"Learning path generation failed: {e}") from e

    path = models.LearningPath(user_id=user.id, subject=subject)
    db.add(path)
    db.flush()
    for i, n in enumerate(nodes_data):
        db.add(models.LearningPathNode(
            path_id=path.id, order_index=i, topic=n.get("topic", ""),
            prerequisite_of=n.get("prerequisite_of"), status="available" if i == 0 else "locked",
        ))
    db.commit()
    db.refresh(path)
    return path


@router.get("/{path_id}", response_model=LearningPathOut)
def get_learning_path(path_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    path = db.get(models.LearningPath, path_id)
    if path is None or path.user_id != user.id:
        raise HTTPException(404, "Learning path not found")
    return path
