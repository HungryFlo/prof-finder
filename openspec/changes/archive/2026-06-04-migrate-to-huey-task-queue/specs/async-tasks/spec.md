## MODIFIED Requirements

### Requirement: Task State Management

系统 SHALL 将任务状态同时存储在内存和 `background_tasks` 表中，以支持服务器重启后的任务恢复。

#### Scenario: Task lifecycle
- **WHEN** 任务创建
- **THEN** 任务状态同时保存在内存 dict 和 `background_tasks` 数据库表中
- **AND** 任务完成或取消后，内存中的状态在 5 分钟后清理
- **AND** 数据库中的记录保留用于审计

#### Scenario: Server restart
- **WHEN** 服务器重启
- **THEN** `background_tasks` 表中状态为 `pending` 或 `running` 的任务被重新加载到内存
- **AND** 任务状态重置为 `pending` 并重新入队执行
- **AND** 已保存到数据库的业务结果不受影响

#### Scenario: Rehydration on startup
- **WHEN** FastAPI lifespan 启动
- **THEN** 调用 `_rehydrate_tasks()` 从 `background_tasks` 加载未完成任务
- **AND** 每个恢复的任务通过 `enqueue_task()` 重新加入 Huey 队列
- **AND** Huey consumer 作为 daemon 线程启动

#### Scenario: Task not found
- **WHEN** 请求不存在的 task_id
- **THEN** 返回 404 错误

## ADDED Requirements

### Requirement: Persistent Task Queue

系统 SHALL 使用 Huey + SQLite 作为任务队列后端，consumer 作为 daemon 线程在 uvicorn 进程内运行。

#### Scenario: Task enqueue
- **WHEN** 任何后台任务被触发（爬取、匹配、生成等）
- **THEN** 任务通过 `enqueue_task()` 加入 Huey SQLite 队列
- **AND** Huey consumer 线程按 FIFO 顺序取出执行

#### Scenario: Consumer thread lifecycle
- **WHEN** FastAPI 应用启动
- **THEN** Huey consumer 作为 daemon 线程启动（默认 2 worker）
- **WHEN** FastAPI 应用关闭
- **THEN** Huey consumer 收到停止信号并优雅退出

#### Scenario: Task executor registration
- **WHEN** 定义新的后台任务类型
- **THEN** executor 函数使用 `@register_task("<task_type>")` 装饰器注册
- **AND** Huey dispatcher 根据 `task_type` 查找并调用对应 executor
