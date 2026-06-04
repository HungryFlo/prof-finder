## 1. OpenSpec（阶段 1）

- [x] 1.1 创建 `proposal.md` / `design.md` / `tasks.md` / spec deltas
- [x] 1.2 `openspec validate migrate-to-huey-task-queue --strict --no-interactive`

## 2. 基础设施（阶段 2）

- [x] 2.1 `pyproject.toml` 添加 `huey` 依赖
- [x] 2.2 `config.py` 添加 `huey_db_path` / `huey_consumer_workers` 配置
- [x] 2.3 创建 `models/background_task.py`（`BackgroundTask` SQLAlchemy 模型）
- [x] 2.4 `db/database.py` 导入新模型，确保 `create_all` 覆盖
- [x] 2.5 创建 `api/task_queue.py`（Huey 实例、consumer 线程管理、task registry、`enqueue_task`）

## 3. task_manager.py 改造（阶段 3）

- [x] 3.1 添加 `_tasks_lock` 线程锁、`persist_task()` DB 持久化
- [x] 3.2 转换 16 个 executor：`async def` → `def`，移除 `asyncio.to_thread`/`asyncio.sleep(0)`，改为 `task_id` 参数
- [x] 3.3 添加 `@register_task()` 装饰器到所有 executor
- [x] 3.4 链式任务改用 `enqueue_task()` 代替 `asyncio.create_task()`
- [x] 3.5 取消逻辑适配：移除 `asyncio.CancelledError`，改用 `TaskCancelled` 异常 + return/break

## 4. 接线（阶段 4）

- [x] 4.1 `main.py` lifespan：`_rehydrate_tasks()` + `start_consumer()` / `stop_consumer()`
- [x] 4.2 5 个 route 文件：`asyncio.create_task(execute_foo(...))` → `enqueue_task(...)`
- [x] 4.3 `routes/tasks.py` cancel：增加 `huey.revoke()`
- [x] 4.4 `cli/professor.py`：`await execute_foo(...)` → `execute_foo(task_id, ...)`

## 5. 测试与验证（阶段 5）

- [x] 5.1 创建 `tests/test_task_queue.py`（17 个测试：CRUD、enqueue/execute、取消、rehydration、线程安全）
- [x] 5.2 更新现有测试（`test_api_profiles.py` sync executor 签名变更）
- [x] 5.3 全量 `pytest` 通过（189 passed, 1 skipped 为网络集成测试，与本次变更无关）
- [x] 5.4 手动测试：启动服务器 → 创建任务 → SSE 进度 → 链式任务 → 重启恢复

## 6. 文档（阶段 6）

- [x] 6.1 `README.md` 添加 Task Queue 架构说明
- [x] 6.2 `openspec validate` 通过
