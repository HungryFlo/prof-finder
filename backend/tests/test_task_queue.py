"""Tests for Huey task queue integration."""

import time
import threading

import pytest

from prof_finder.api.task_manager import (
    TaskStatus,
    TaskCancelled,
    TaskState,
    create_task,
    get_task,
    get_user_tasks,
    persist_task,
    cleanup_old_tasks,
    _tasks,
    _tasks_lock,
)
from prof_finder.api.task_queue import (
    huey,
    register_task,
    enqueue_task,
    TASK_REGISTRY,
    start_consumer,
    stop_consumer,
)
from prof_finder.models.background_task import BackgroundTask


class TestBackgroundTaskModel:
    """Tests for BackgroundTask SQLAlchemy model."""

    def test_create_and_read_row(self, test_db):
        """BackgroundTask row can be created and read back."""
        with test_db.session() as session:
            bt = BackgroundTask(
                task_id="test-uuid-001",
                task_type="test-type",
                task_name="Test Task",
                user_id=1,
                status="pending",
                total=5,
            )
            session.add(bt)
            session.commit()

            row = (
                session.query(BackgroundTask)
                .filter(BackgroundTask.task_id == "test-uuid-001")
                .first()
            )
            assert row is not None
            assert row.task_type == "test-type"
            assert row.task_name == "Test Task"
            assert row.status == "pending"

    def test_unique_task_id(self, test_db):
        """task_id must be unique."""
        with test_db.session() as session:
            session.add(BackgroundTask(task_id="uniq-1", task_type="t", task_name="n", user_id=1, total=1))
            session.commit()

        # Second insert with same task_id should fail
        session = test_db.SessionLocal()
        try:
            session.add(BackgroundTask(task_id="uniq-1", task_type="t", task_name="n", user_id=1, total=1))
            with pytest.raises(Exception):
                session.flush()
                session.commit()
        finally:
            session.rollback()
            session.close()

    def test_results_json_roundtrip(self, test_db):
        """results field handles JSON serialization."""
        results = [{"name": "Prof. X", "success": True}, {"name": "Prof. Y", "success": False}]
        with test_db.session() as session:
            bt = BackgroundTask(
                task_id="json-test", task_type="t", task_name="n", user_id=1, total=2, results=results,
            )
            session.add(bt)
            session.commit()

            row = session.query(BackgroundTask).filter(BackgroundTask.task_id == "json-test").first()
            assert row.results == results


class TestTaskRegistry:
    """Tests for create_task / get_task / get_user_tasks / persist_task."""

    def test_create_task_in_memory_and_db(self, test_db, monkeypatch):
        """create_task adds to both in-memory dict and DB."""
        monkeypatch.setattr("prof_finder.db.database._db", test_db, raising=False)

        task = create_task("test-type", "Memory+DB", user_id=1, total=3)
        assert task.task_type == "test-type"
        assert task.status == TaskStatus.PENDING

        # Check in-memory
        assert get_task(task.task_id) is task

        # Check DB
        with test_db.session() as session:
            row = (
                session.query(BackgroundTask)
                .filter(BackgroundTask.task_id == task.task_id)
                .first()
            )
            assert row is not None
            assert row.task_name == "Memory+DB"

    def test_get_task_returns_none_for_unknown_id(self):
        """get_task returns None for unknown task_id."""
        assert get_task("nonexistent-id") is None

    def test_get_user_tasks_filters_by_user_and_status(self):
        """get_user_tasks returns only PENDING/RUNNING/FAILED tasks for the given user."""
        t1 = create_task("t", "A1", user_id=1, total=1)
        t2 = create_task("t", "A2", user_id=1, total=1)
        t3 = create_task("t", "B", user_id=2, total=1)

        # Mark t1 completed (should not appear)
        t1.status = TaskStatus.COMPLETED

        tasks = get_user_tasks(1)
        ids = {t.task_id for t in tasks}
        assert t2.task_id in ids  # PENDING, shows
        assert t1.task_id not in ids  # COMPLETED, hidden
        assert t3.task_id not in ids  # different user

    def test_persist_task_updates_existing_row(self, test_db, monkeypatch):
        """persist_task updates the DB row with current in-memory state."""
        monkeypatch.setattr("prof_finder.db.database._db", test_db, raising=False)

        task = create_task("t", "Persistence", user_id=1, total=10)
        task.status = TaskStatus.RUNNING
        task.current = 5
        task.message = "processing..."
        persist_task(task)

        with test_db.session() as session:
            row = (
                session.query(BackgroundTask)
                .filter(BackgroundTask.task_id == task.task_id)
                .first()
            )
            assert row.status == "running"
            assert row.current == 5
            assert row.message == "processing..."

    def test_cleanup_old_tasks_removes_completed(self):
        """cleanup_old_tasks removes completed tasks older than 5 minutes."""
        task = create_task("t", "Old", user_id=1, total=1)
        task.status = TaskStatus.COMPLETED
        # Fake an old creation time
        from datetime import datetime, timezone, timedelta

        task.created_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        assert get_task(task.task_id) is not None
        cleanup_old_tasks()
        assert get_task(task.task_id) is None

    def test_thread_safety_concurrent_access(self):
        """Concurrent reads/writes to _tasks dict do not corrupt."""
        errors = []

        def writer():
            try:
                for i in range(100):
                    tid = f"concurrent-{i}"
                    with _tasks_lock:
                        _tasks[tid] = TaskState(
                            task_id=tid, task_type="t", task_name="n",
                            user_id=1, status=TaskStatus.PENDING, total=1,
                        )
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(500):
                    with _tasks_lock:
                        list(_tasks.values())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(3)] + [
            threading.Thread(target=reader) for _ in range(3)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors


class TestEnqueueAndExecute:
    """Tests for enqueue_task and executor registration."""

    def test_register_task_decorator(self):
        """@register_task adds the function to TASK_REGISTRY."""
        @register_task("my-test-task")
        def fake_executor(task_id: str, value: int):
            task = get_task(task_id)
            if task:
                task.status = TaskStatus.COMPLETED
                task.message = f"done: {value}"

        assert "my-test-task" in TASK_REGISTRY
        assert TASK_REGISTRY["my-test-task"] is fake_executor
        # Cleanup
        del TASK_REGISTRY["my-test-task"]

    def test_enqueue_and_execute_immediate(self, test_db):
        """In immediate mode, tasks execute synchronously."""
        huey.immediate = True
        try:
            @register_task("immediate-test")
            def handler(task_id: str, message: str):
                task = get_task(task_id)
                task.status = TaskStatus.COMPLETED
                task.message = message

            task = create_task("immediate-test", "Immediate", user_id=1, total=1)
            enqueue_task("immediate-test", task.task_id, "hello")

            refreshed = get_task(task.task_id)
            assert refreshed.status == TaskStatus.COMPLETED
            assert refreshed.message == "hello"
        finally:
            huey.immediate = False
            TASK_REGISTRY.pop("immediate-test", None)

    def test_enqueue_task_stores_huey_result_id(self):
        """enqueue_task stores the Huey result ID for later revocation."""
        huey.immediate = True
        try:
            @register_task("rid-test")
            def handler(task_id: str):
                pass

            task = create_task("rid-test", "RID", user_id=1, total=1)
            enqueue_task("rid-test", task.task_id)

            refreshed = get_task(task.task_id)
            assert refreshed is not None
            assert refreshed.huey_result_id is not None
        finally:
            huey.immediate = False
            TASK_REGISTRY.pop("rid-test", None)

    def test_cancellation_flag_stops_executor(self):
        """Setting cancel_requested stops the loop in an executor."""
        huey.immediate = True
        try:
            @register_task("cancel-test")
            def handler(task_id: str, items: list):
                task = get_task(task_id)
                task.status = TaskStatus.RUNNING
                for item in items:
                    if task.cancel_requested:
                        task.status = TaskStatus.CANCELLED
                        return
                    task.success_count += 1

            task = create_task("cancel-test", "Cancel me", user_id=1, total=5)
            # Pre-set cancel flag
            task.cancel_requested = True

            enqueue_task("cancel-test", task.task_id, list(range(100)))
            refreshed = get_task(task.task_id)
            assert refreshed.status == TaskStatus.CANCELLED
            assert refreshed.success_count == 0
        finally:
            huey.immediate = False
            TASK_REGISTRY.pop("cancel-test", None)

    def test_executor_unknown_task_type(self):
        """Calling a non-existent task_type logs an error but does not crash."""
        huey.immediate = True
        try:
            # Unknown task type should not raise
            enqueue_task("nonexistent-task-type", "fake-id")
        finally:
            huey.immediate = False

    def test_chained_task_enqueuing(self):
        """Parent task enqueues child task via enqueue_task."""
        huey.immediate = True
        try:
            @register_task("chain-parent")
            def parent(task_id: str, child_name: str):
                task = get_task(task_id)
                task.status = TaskStatus.RUNNING
                child = create_task("chain-child", child_name, user_id=task.user_id, total=1)
                enqueue_task("chain-child", child.task_id, value=42)
                task.status = TaskStatus.COMPLETED

            @register_task("chain-child")
            def child(task_id: str, value: int):
                task = get_task(task_id)
                task.status = TaskStatus.COMPLETED
                task.message = f"value={value}"

            t = create_task("chain-parent", "Parent", user_id=1, total=1)
            enqueue_task("chain-parent", t.task_id, "ChildTask")

            # Both should be done (immediate mode)
            parent_t = get_task(t.task_id)
            assert parent_t.status == TaskStatus.COMPLETED

            # Find the child task
            children = [t for t in _tasks.values() if t.task_type == "chain-child"]
            assert len(children) == 1
            assert children[0].status == TaskStatus.COMPLETED
            assert children[0].message == "value=42"
        finally:
            huey.immediate = False
            TASK_REGISTRY.pop("chain-parent", None)
            TASK_REGISTRY.pop("chain-child", None)


class TestConsumerManagement:
    """Tests for start_consumer / stop_consumer lifecycle."""

    def test_start_and_stop_consumer(self, tmp_path, monkeypatch):
        """Consumer starts and stops without errors."""
        import tempfile
        import os

        # Use a temporary file for the Huey DB so it doesn't interfere
        huey_db = tmp_path / "huey_test.db"
        monkeypatch.setattr(
            "prof_finder.api.task_queue.huey.storage._filename",
            str(huey_db),
            raising=False,
        )
        start_consumer()
        time.sleep(0.1)
        stop_consumer()


class TestRehydration:
    """Tests for task rehydration from DB on startup."""

    def test_rehydrate_loads_pending_tasks(self, test_db, monkeypatch):
        """_rehydrate_tasks loads PENDING tasks from DB into memory."""
        monkeypatch.setattr("prof_finder.db.database._db", test_db, raising=False)

        from prof_finder.api.main import _rehydrate_tasks

        # Create a DB row for a pending task
        with test_db.session() as session:
            bt = BackgroundTask(
                task_id="rehydrate-pending",
                task_type="batch-crawl",
                task_name="Recovered Task",
                user_id=1,
                status="pending",
                total=10,
            )
            session.add(bt)
            session.commit()

        _rehydrate_tasks()

        task = get_task("rehydrate-pending")
        assert task is not None
        assert task.task_name == "Recovered Task"
        assert task.status == TaskStatus.PENDING
        assert task.total == 10
