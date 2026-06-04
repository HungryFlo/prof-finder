## Context
The project uses SQLite for all data storage and targets non-technical users who run everything locally. Adding Redis or a separate worker process would break the simple install story. Huey's `SqliteHuey` backend provides persistent task queuing with zero additional infrastructure.

## Goals / Non-Goals
- **Goals**: Persistent tasks that survive restarts, proper FIFO queue, crash recovery, same single-process install.
- **Non-Goals**: Distributed workers, task prioritization, scheduled/periodic tasks, multi-user queue isolation.

## Architecture

```
[FastAPI Event Loop]         [Huey Consumer Thread (daemon, 2 workers)]
     |                              |
     |-- enqueue_task() ----------->|
     |                              |-- _huey_run_task() dispatcher
     |                              |   |-- @register_task("batch-crawl")
     |                              |   |-- @register_task("match")
     |                              |   '-- ... (17 executors)
     |                              |
     |-- SSE polls _tasks dict <----|-- updates task.current, task.message, etc.
     |
     |-- persist_task() writes ---->|-- BackgroundTask DB row
```

## Decisions

1. **Single `@huey.task()` dispatcher** rather than 17 separate task types. Avoids import-ordering issues and keeps the registry simple.
2. **Separate Huey DB** (`data/huey_tasks.db` by default) rather than sharing `prof_finder.db`. Huey manages its own tables (queue, results, schedule); isolating them prevents schema conflicts.
3. **Consumer thread** with `workers=2` runs as daemon. Two workers allow one long-running task (LLM call) while the second picks up other tasks.
4. **Hybrid state**: in-memory `_tasks` dict for SSE speed + DB `background_tasks` table for persistence. The dict is primary during execution; DB is used for rehydration on startup and cross-thread visibility.
5. **Tasks reset to PENDING on rehydration**. Mid-execution state (file handles, HTTP requests) cannot be recovered, so restart = fresh execution.
6. **Cancellation**: `cancel_requested` flag (same as today) for running tasks + `huey.revoke()` for pending tasks not yet started.

## Data Flow

1. Route handler calls `create_task()` → `TaskState` in memory + `BackgroundTask` row in DB
2. Route handler calls `enqueue_task(task_type, task_id, ...)` → Huey enqueues
3. Route returns `TaskStartResponse(task_id=...)` to frontend
4. Frontend opens SSE → polls `_tasks[task_id]` every 500ms
5. Huey consumer picks up task → dispatches to registered executor
6. Executor updates `task.current`, `task.message`, etc. in memory + DB
7. SSE emits progress events → frontend updates progress bar
8. Task completes → SSE emits terminal event → frontend shows result

## Risks / Trade-offs
- **Daemon thread dies with process**: Acceptable for local use; tasks rehydrate on restart.
- **SQLite contention**: Huey consumer and FastAPI may write to different DBs simultaneously. SQLite WAL mode handles concurrent reads + one writer. If contention becomes visible, increase Huey's `poll_delay`.
- **Sync executors block consumer thread**: The consumer has 2 workers, so one blocked worker doesn't block all tasks. LLM calls and HTTP crawls are expected to block; that's why `asyncio.to_thread()` existed. The thread-based consumer is equivalent.
