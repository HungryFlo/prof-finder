"""Huey task queue initialization, consumer management, and task registry."""

import threading
from typing import Any, Callable, Dict, List, Optional

from huey import SqliteHuey
from huey.consumer import Consumer

from ..config import settings

# ---------------------------------------------------------------------------
# Huey instance
# ---------------------------------------------------------------------------
huey = SqliteHuey(
    name="prof-finder",
    filename=settings.huey_db_path,
)

# ---------------------------------------------------------------------------
# Task executor registry
# ---------------------------------------------------------------------------
TASK_REGISTRY: Dict[str, Callable] = {}


def register_task(task_type: str):
    """Decorator that registers an executor function for a given task type."""

    def decorator(func: Callable) -> Callable:
        TASK_REGISTRY[task_type] = func
        return func

    return decorator


# ---------------------------------------------------------------------------
# Generic Huey task dispatcher
# ---------------------------------------------------------------------------
@huey.task()
def _huey_run_task(task_type: str, task_id: str, args: List[Any], kwargs: Dict[str, Any]):
    """Dispatcher: looks up the registered executor and calls it in the consumer thread.

    All task types share this single ``@huey.task()`` wrapper so that we can
    keep the registry flat and avoid import-ordering problems between the
    Huey instance and the executor module.
    """
    executor = TASK_REGISTRY.get(task_type)
    if executor is None:
        import logging

        logging.getLogger(__name__).error("Unknown task type: %s", task_type)
        return
    executor(task_id, *args, **kwargs)


def enqueue_task(task_type: str, task_id: str, *args, **kwargs):
    """Enqueue a background task for execution via Huey.

    Route handlers and chained tasks call this instead of
    ``asyncio.create_task()``.  Returns the Huey result and stores
    ``result.id`` on the TaskState for later revocation.
    """
    args_list = list(args)
    result = _huey_run_task(task_type, task_id, args_list, kwargs)
    # Store Huey result ID and args so /api/tasks/{id}/cancel can revoke
    # and _rehydrate_tasks can re-enqueue with the same args.
    from .task_manager import get_task, persist_task

    task = get_task(task_id)
    if task:
        task.huey_result_id = result.id
        task.enqueue_args = args_list
        task.enqueue_kwargs = kwargs
        persist_task(task)
    return result


# ---------------------------------------------------------------------------
# Consumer thread management
# ---------------------------------------------------------------------------
_consumer: Optional[Consumer] = None
_consumer_thread: Optional[threading.Thread] = None


class _ThreadConsumer(Consumer):
    """Consumer that skips signal handler setup when running in a daemon thread."""

    def _set_signal_handlers(self):
        # Daemon threads cannot register signal handlers.
        # The consumer is stopped via stop_consumer() instead.
        pass


def start_consumer():
    """Start the Huey consumer in a background daemon thread."""
    global _consumer, _consumer_thread
    if _consumer is not None:
        return  # already started

    _consumer = _ThreadConsumer(
        huey,
        workers=settings.huey_consumer_workers,
        periodic=False,
    )
    _consumer_thread = threading.Thread(
        target=_consumer.run,
        daemon=True,
        name="huey-consumer",
    )
    _consumer_thread.start()


def stop_consumer():
    """Signal the Huey consumer to shut down gracefully."""
    global _consumer, _consumer_thread
    if _consumer is not None:
        _consumer.stop()
        _consumer = None
    if _consumer_thread is not None:
        _consumer_thread.join(timeout=5)
        _consumer_thread = None
