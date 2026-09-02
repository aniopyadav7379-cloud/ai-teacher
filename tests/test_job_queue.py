import pytest

from backend.jobs.queue import get_job_queue, InProcessQueue


class FakeBackgroundTasks:
    def __init__(self):
        self.calls = []

    def add_task(self, func, *args):
        self.calls.append((func, args))


def _dummy_job(x, y):
    return x + y


def test_default_backend_is_inprocess(monkeypatch):
    from backend.core import config
    config.get_settings.cache_clear()
    monkeypatch.delenv("JOB_QUEUE_BACKEND", raising=False)

    bg = FakeBackgroundTasks()
    queue = get_job_queue(bg)
    assert isinstance(queue, InProcessQueue)


def test_inprocess_queue_enqueues_onto_background_tasks():
    bg = FakeBackgroundTasks()
    queue = InProcessQueue(bg)
    queue.enqueue(_dummy_job, 1, 2)
    assert bg.calls == [(_dummy_job, (1, 2))]


def test_inprocess_queue_requires_background_tasks_instance():
    with pytest.raises(ValueError):
        InProcessQueue(None)
