"""
Job queue abstraction (limitation #5).

FastAPI's BackgroundTasks runs work in the same process, after the response
is sent — fine for a single-node dev deployment, but it doesn't survive a
process restart mid-job, doesn't retry on failure, and doesn't let you scale
ingestion/media-generation workers independently of the API. This module
makes that swap a one-line config change instead of a rewrite: every call
site (materials upload, video generation) enqueues through this interface,
never through `BackgroundTasks.add_task` directly.

Two backends:
  - "inprocess" (default): wraps FastAPI's BackgroundTasks. Zero extra
    infrastructure — what every route already used before this change.
  - "rq": Redis Queue. Production-capable — persists jobs in Redis, retries,
    runs in separate worker processes (see workers/worker.py and the `redis`
    + `worker` services in docker-compose.yml).

Jobs are enqueued by (module_path, function_name, args) rather than by
passing a closure, because RQ needs to pickle a reference it can re-import
in the worker process — a lambda or bound method can't cross that boundary.
"""
from __future__ import annotations
import abc
import importlib
from typing import Callable, Any

from backend.core.config import get_settings


class JobQueue(abc.ABC):
    @abc.abstractmethod
    def enqueue(self, func: Callable, *args: Any) -> None:
        """Schedule `func(*args)` to run outside the current request."""


class InProcessQueue(JobQueue):
    """Wraps FastAPI's BackgroundTasks. `background_tasks` must be the
    request-scoped object from the route (via `Depends`/parameter injection)."""

    def __init__(self, background_tasks):
        if background_tasks is None:
            raise ValueError(
                "InProcessQueue requires a FastAPI BackgroundTasks instance. "
                "Pass it from the route, or switch JOB_QUEUE_BACKEND=rq for a "
                "worker-based queue that doesn't need one."
            )
        self._bg = background_tasks

    def enqueue(self, func: Callable, *args: Any) -> None:
        self._bg.add_task(func, *args)


class RQQueue(JobQueue):
    """Redis-backed production queue. Jobs run in a separate `rq worker`
    process (workers/worker.py), so they survive API-process restarts and
    can be scaled/retried independently."""

    def __init__(self):
        from redis import Redis
        from rq import Queue

        settings = get_settings()
        self._redis = Redis.from_url(settings.redis_url)
        self._queue = Queue("ai_teacher", connection=self._redis)

    def enqueue(self, func: Callable, *args: Any) -> None:
        # Enqueue by importable reference (module:function), not a closure —
        # required so the separate worker process can deserialize the job.
        ref = f"{func.__module__}.{func.__qualname__}"
        self._queue.enqueue(ref, *args)


def get_job_queue(background_tasks=None) -> JobQueue:
    settings = get_settings()
    if settings.job_queue_backend == "rq":
        return RQQueue()
    return InProcessQueue(background_tasks)
