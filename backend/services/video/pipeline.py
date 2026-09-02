"""
AI TEACHING VIDEO pipeline (spec section 14):

  Lesson concept -> Teaching Script -> Voice Generation -> Avatar Generation
  -> Assembly -> Final Teaching Video

Runs as a background task (spec section 24) so uploads/lesson generation
never block on media rendering. Progress is tracked via TeachingVideo.status
so the frontend can show real progress states, not a fake spinner.
"""
from __future__ import annotations
from pathlib import Path

from sqlalchemy.orm import Session

from backend import models
from backend.core.config import get_settings
from backend.services.tts.factory import get_tts_provider
from backend.services.avatar.factory import get_avatar_provider


def build_teaching_script(concept: models.LessonConcept) -> str:
    """Turns the planned explanation/analogy/example into a spoken script."""
    parts = [concept.explanation]
    if concept.analogy:
        parts.append(f"Think of it like this: {concept.analogy}")
    if concept.example:
        parts.append(f"For example: {concept.example}")
    return " ".join(p.strip() for p in parts if p.strip())


async def generate_teaching_video(db: Session, concept_id: str, language: str) -> None:
    """Full media pipeline for one concept. Never raises — all failures are
    recorded on the TeachingVideo row so the UI can show a real error state."""
    concept = db.get(models.LessonConcept, concept_id)
    if concept is None:
        return

    video = concept.video
    if video is None:
        video = models.TeachingVideo(concept_id=concept_id)
        db.add(video)
        db.commit()
        db.refresh(video)

    settings = get_settings()
    media_dir = Path(settings.media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Script
        video.script = build_teaching_script(concept)
        video.status = "script_ready"
        db.commit()

        # 2. Voice
        tts = get_tts_provider()
        tts_result = await tts.synthesize(video.script, language=language)
        audio_path = media_dir / f"{video.id}.mp3"
        audio_path.write_bytes(tts_result.audio_bytes)
        video.audio_url = f"/media/{audio_path.name}"
        video.status = "voice_ready"
        db.commit()

        # 3. Avatar (may be synchronous-fake "ready" for the browser-avatar
        # fallback, or an async job id for a cloud provider like D-ID).
        avatar = get_avatar_provider()
        avatar_result = await avatar.generate_video(audio_url=video.audio_url, script_text=video.script)
        video.provider = type(avatar).__name__
        if avatar_result.status == "ready":
            video.avatar_video_url = avatar_result.video_url  # None => browser renders live from audio_url
            video.status = "ready"
        else:
            # Async provider: store the job id in provider field's companion and mark assembling.
            # A polling endpoint (see api/routes/teaching.py) checks status later.
            video.status = "assembling"
            video.error_message = None
            video.avatar_video_url = None
            video.provider = f"{video.provider}:{avatar_result.provider_job_id}"
        db.commit()

    except Exception as e:  # noqa: BLE001 — media pipeline stage must not crash the app
        video.status = "failed"
        video.error_message = str(e)
        db.commit()


async def poll_avatar_status(db: Session, concept_id: str) -> models.TeachingVideo | None:
    """For async avatar providers: check job status and update the video record."""
    concept = db.get(models.LessonConcept, concept_id)
    if concept is None or concept.video is None:
        return None
    video = concept.video
    if video.status != "assembling" or ":" not in (video.provider or ""):
        return video

    from backend.services.avatar.factory import get_avatar_provider

    _, job_id = video.provider.split(":", 1)
    avatar = get_avatar_provider()
    result = await avatar.check_status(job_id)
    if result.status == "ready":
        video.avatar_video_url = result.video_url
        video.status = "ready"
        db.commit()
    elif result.status == "failed":
        video.status = "failed"
        video.error_message = "Avatar provider reported failure."
        db.commit()
    return video
