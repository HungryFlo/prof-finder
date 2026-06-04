# Change: Migrate Task Queue to Huey + SQLite

## Why
The current background task system uses an in-memory `Dict[str, TaskState]` + `asyncio.create_task()`. Tasks are lost on server restart, there are no queue semantics (FIFO ordering, backpressure), and long task chains (crawl → enrichment → profile generation) are fragile. The system needs persistent, reliable background task execution while maintaining the simple single-process installation story for non-technical users.

## What Changes
- Introduce **Huey** with **SQLite backend** (`SqliteHuey`) as the task queue.
- Huey consumer runs as a **daemon thread inside the uvicorn process** — no separate worker process or Redis required.
- Task state is stored in both an **in-memory dict** (for fast SSE reads, as today) and a new **`BackgroundTask` SQLAlchemy model** (for persistence across restarts).
- Convert all 17 async executor coroutines to **synchronous functions** registered via `@register_task()`, dispatched through a single `@huey.task()` wrapper.
- On server startup, **rehydrate** any PENDING/RUNNING tasks from the `background_tasks` table back into memory and re-enqueue them.
- SSE endpoint, frontend task store, and API surface remain **unchanged**.

## Impact
- Affected specs: `async-tasks`, `data-model`
- Affected code: `task_manager.py` (all executors), 5 route files, `main.py`, `config.py`, `database.py`, `cli/professor.py`, `pyproject.toml`
- New files: `task_queue.py`, `models/background_task.py`
- No frontend changes required
