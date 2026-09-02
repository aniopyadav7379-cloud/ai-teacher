"""
RQ worker entrypoint — only used when JOB_QUEUE_BACKEND=rq.

Runs ingestion (document processing) and media-generation jobs enqueued by
backend/jobs/queue.py's RQQueue. Scale this independently of the API by
running more replicas of this process (see docker-compose.yml's `worker`
service) — ingestion and video generation are the two operations expensive
enough to want their own worker pool separate from request-handling.

Run directly with:  python -m workers.worker
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from redis import Redis
from rq import Worker, Queue

from backend.core.config import get_settings


def main():
    settings = get_settings()
    conn = Redis.from_url(settings.redis_url)
    queue = Queue("ai_teacher", connection=conn)
    worker = Worker([queue], connection=conn)
    worker.work()


if __name__ == "__main__":
    main()
