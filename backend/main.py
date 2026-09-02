from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from backend.core.config import get_settings
from backend.database.session import init_db
from backend.api.routes import (
    auth, sessions, materials, topics, lessons, questions, teaching, assessment, progress, learning_path, student,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    if settings.app_env != "development" and settings.secret_key == "dev-only-not-secure":
        raise RuntimeError(
            "SECRET_KEY is still set to the development placeholder while APP_ENV != 'development'. "
            "Set a real random SECRET_KEY in .env before running in any non-development environment — "
            "refusing to start with a guessable JWT signing key."
        )
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.vector_db_path).mkdir(parents=True, exist_ok=True)
    init_db()
    yield
    # --- shutdown --- (nothing to clean up currently; hook is here if that changes)


app = FastAPI(
    title="AI Teacher API",
    description="Personalized, adaptive AI teaching platform — RAG lesson planning, "
                 "the UNDERSTAND->PLAN->EXPLAIN->QUESTION->EVALUATE->ADAPT->ASSESS teaching loop, "
                 "and pluggable voice/avatar media generation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Development: wide open, zero-friction local work against the Vite dev server.
    # Any other environment: explicit allowlist only (fails closed by default —
    # an empty CORS_ALLOWED_ORIGINS means no cross-origin requests succeed,
    # rather than silently allowing everything). Required when frontend and
    # backend are deployed on different origins (e.g. separate hosts, not
    # behind the bundled nginx proxy in docker-compose.yml).
    allow_origins=["*"] if settings.app_env == "development" else [
        o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces / secrets to the client (spec section 23).
    return JSONResponse(status_code=500, content={"detail": "Internal server error. Please try again."})


Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(materials.router)
app.include_router(topics.router)
app.include_router(lessons.router)
app.include_router(questions.router)
app.include_router(teaching.router)
app.include_router(assessment.router)
app.include_router(progress.router)
app.include_router(learning_path.router)
app.include_router(student.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
