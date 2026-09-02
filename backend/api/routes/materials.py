import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.core.security import get_current_user
from backend.core.config import get_settings
from backend import models
from backend.schemas.schemas import MaterialOut
from backend.services.rag.ingestion import ingest_material
from backend.jobs.queue import get_job_queue

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.post("/upload", response_model=MaterialOut, status_code=201)
async def upload_material(
    session_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    session = db.get(models.LearningSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "Session not found")

    settings = get_settings()
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {sorted(settings.ALLOWED_UPLOAD_EXTENSIONS)}")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(400, f"File too large ({size_mb:.1f}MB). Max is {settings.max_upload_mb}MB.")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}{ext}"
    dest = upload_dir / safe_name
    dest.write_bytes(contents)

    material = models.UploadedMaterial(
        session_id=session_id,
        filename=file.filename or safe_name,
        file_path=str(dest),
        file_type=ext.lstrip("."),
        status="uploaded",
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    get_job_queue(background_tasks).enqueue(_run_ingestion, material.id)
    return material


def _run_ingestion(material_id: str):
    # Module-level and side-effect-free w.r.t. request state (opens its own
    # DB session) so it can run either in-process (BackgroundTasks) or in a
    # separate RQ worker process — see backend/jobs/queue.py.
    import asyncio
    from backend.database.session import SessionLocal

    db = SessionLocal()
    try:
        material = db.get(models.UploadedMaterial, material_id)
        if material:
            asyncio.run(ingest_material(db, material))
    finally:
        db.close()


@router.get("/{material_id}", response_model=MaterialOut)
def get_material(material_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    material = db.get(models.UploadedMaterial, material_id)
    if material is None:
        raise HTTPException(404, "Material not found")
    return material


@router.get("/session/{session_id}", response_model=list[MaterialOut])
def list_session_materials(session_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.UploadedMaterial).filter_by(session_id=session_id).all()
