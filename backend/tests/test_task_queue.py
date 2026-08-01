"""Task registry and enqueue bookkeeping."""

from __future__ import annotations

import pytest

from prof_finder.api import task_queue as tq


@pytest.fixture
def isolated_huey(tmp_path, monkeypatch, temp_db):
    """A Huey instance backed by a throwaway SQLite file, with no consumer running."""
    from prof_finder.config import settings

    monkeypatch.setattr(settings, "huey_db_path", str(tmp_path / "huey.db"))
    monkeypatch.setattr(tq, "_huey", None)
    monkeypatch.setattr(tq, "_huey_run_task_fn", None)
    monkeypatch.setattr(tq, "TASK_REGISTRY", dict(tq.TASK_REGISTRY))
    yield tq._ensure_huey()


def test_register_task_adds_to_the_registry(isolated_huey):
    @tq.register_task("unit-test-task")
    def executor(task_id):  # pragma: no cover - registration only
        return task_id

    assert tq.TASK_REGISTRY["unit-test-task"] is executor


def test_registering_the_same_type_twice_replaces_the_executor(isolated_huey):
    @tq.register_task("dup")
    def first(task_id):  # pragma: no cover
        return "first"

    @tq.register_task("dup")
    def second(task_id):  # pragma: no cover
        return "second"

    assert tq.TASK_REGISTRY["dup"] is second


def test_all_shipped_task_types_are_registered(isolated_huey):
    import prof_finder.api.task_manager  # noqa: F401  (registers executors on import)

    for task_type in ("match", "batch-crawl", "single-crawl", "single-letter"):
        assert task_type in tq.TASK_REGISTRY


def test_unknown_task_type_is_logged_not_raised(isolated_huey, caplog):
    tq._huey_run_task("no-such-type", "task-1", [], {})
    assert "Unknown task type" in caplog.text


def test_dispatcher_forwards_args_and_kwargs(isolated_huey):
    seen = {}

    @tq.register_task("echo")
    def executor(task_id, *args, **kwargs):
        seen["call"] = (task_id, args, kwargs)

    tq._huey_run_task("echo", "task-2", [1, 2], {"flag": True})
    assert seen["call"] == ("task-2", (1, 2), {"flag": True})


def test_enqueue_records_replay_arguments_on_the_task(isolated_huey):
    from prof_finder.api.task_manager import create_task, get_task

    @tq.register_task("replayable")
    def executor(task_id, value):  # pragma: no cover - never consumed here
        return value

    task = create_task("replayable", "Replayable", user_id=1, total=1)
    tq.enqueue_task("replayable", task.task_id, 42, mode="fast")

    stored = get_task(task.task_id)
    assert stored.enqueue_args == [42]
    assert stored.enqueue_kwargs == {"mode": "fast"}
    assert stored.huey_result_id


def test_flush_queue_drops_pending_jobs(isolated_huey):
    from prof_finder.api.task_manager import create_task

    @tq.register_task("flushable")
    def executor(task_id):  # pragma: no cover - never consumed here
        return None

    task = create_task("flushable", "Flushable", user_id=1, total=1)
    tq.enqueue_task("flushable", task.task_id)
    assert len(isolated_huey) == 1

    tq.flush_queue()
    assert len(isolated_huey) == 0
