"""
Central application configuration.

All secrets/config come from environment variables (never hardcoded).
See .env.example for the full documented list.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    app_env: str = "development"
    secret_key: str = "dev-only-not-secure"
    database_url: str = "sqlite:///./ai_teacher.db"

    # Comma-separated list of allowed frontend origins for CORS, e.g.
    # "https://app.example.com,https://staging.example.com". In development,
    # "*" is used regardless of this value (see main.py) for zero-friction
    # local dev; in any other APP_ENV this MUST be set explicitly, or the
    # API will reject all cross-origin requests (fails closed, not open).
    cors_allowed_origins: str = ""

    vector_db_path: str = "./data/chroma"
    upload_dir: str = "./data/uploads"
    media_dir: str = "./data/media"
    max_upload_mb: int = 50

    # LLM
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Embeddings
    embedding_provider: str = "openai"
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"

    # TTS
    tts_provider: str = "elevenlabs"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id_en: str = "21m00Tcm4TlvDq8ikWAM"
    elevenlabs_voice_id_hi: str = ""

    # Avatar / Video
    avatar_provider: str = "did"
    did_api_key: str = ""
    did_presenter_image_url: str = ""

    # Auth
    access_token_expire_minutes: int = 1440

    # Job queue: "inprocess" (FastAPI BackgroundTasks, zero setup) or "rq"
    # (Redis-backed, production-capable — see backend/jobs/queue.py)
    job_queue_backend: str = "inprocess"
    redis_url: str = "redis://localhost:6379/0"

    # Self-hosted media sidecar endpoints (only used if TTS_PROVIDER=local_realtimevoicechat
    # or AVATAR_PROVIDER=local_linlytalker — see docs/self_hosted_media.md).
    # Configurable rather than hardcoded so a Docker/k8s deployment can point
    # these at a service name instead of localhost.
    local_tts_endpoint: str = "http://localhost:8001"
    local_avatar_endpoint: str = "http://localhost:8002"

    ALLOWED_UPLOAD_EXTENSIONS: set[str] = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".md"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
