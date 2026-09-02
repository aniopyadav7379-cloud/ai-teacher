from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.core.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session and guarantees close()."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables via SQLAlchemy's create_all — used for local/dev
    (particularly zero-setup SQLite dev, where a migration tool is overkill).
    For Postgres/production deployments, use Alembic instead (see
    backend/alembic/ — `alembic upgrade head`, which the Docker image runs
    automatically on container start; see backend/Dockerfile's CMD).
    create_all() is idempotent and a no-op on tables that already exist, so
    calling this after `alembic upgrade head` has already run is harmless.
    """
    from backend import models  # noqa: F401 ensures models are registered on Base.metadata
    Base.metadata.create_all(bind=engine)
