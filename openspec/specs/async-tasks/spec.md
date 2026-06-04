# async-tasks Specification

## Purpose

定义长时间后台任务的执行与可观测性：通过 Huey（`SqliteHuey`）在 uvicorn 进程内消费任务队列，结合内存状态与 `background_tasks` 表持久化；通过 SSE 向客户端推送进度，并支持重启后恢复未完成任务。
## Requirements
### Requirement: Task Progress via SSE

系统 SHALL 使用 Server-Sent Events (SSE) 提供长时间任务的进度通知。

#### Scenario: Start async task
- **WHEN** 用户发起批量操作（批量爬取教授、批量生成邮件）
- **THEN** 创建任务并返回 `task_id`
- **AND** 任务在后台异步执行

#### Scenario: Subscribe to progress
- **WHEN** 客户端连接 SSE 端点 `GET /api/tasks/{task_id}/progress`
- **THEN** 服务端推送进度事件流
- **AND** 每完成一项子任务推送一次更新

#### Scenario: Progress event format
- **WHEN** 推送进度事件
- **THEN** 事件格式为：
  ```
  event: progress
  data: {"current": 5, "total": 20, "status": "running", "message": "正在处理...", "item": {...}}
  ```

#### Scenario: Complete event
- **WHEN** 任务完成（成功或部分失败）
- **THEN** 推送完成事件：
  ```
  event: complete
  data: {"status": "completed", "success_count": 18, "failed_count": 2, "results": [...]}
  ```
- **AND** 关闭 SSE 连接

#### Scenario: Error event
- **WHEN** 任务发生致命错误无法继续
- **THEN** 推送错误事件：
  ```
  event: error
  data: {"status": "failed", "message": "错误原因"}
  ```

---

### Requirement: Task Cancellation

系统 SHALL 支持取消正在执行的任务。

#### Scenario: Cancel task
- **WHEN** 用户请求取消任务 `POST /api/tasks/{task_id}/cancel`
- **THEN** 标记任务为取消状态
- **AND** 当前正在处理的项目完成后停止
- **AND** 已完成的结果保存到数据库

#### Scenario: Cancel event
- **WHEN** 任务被取消
- **THEN** 推送取消事件：
  ```
  event: cancelled
  data: {"status": "cancelled", "completed_count": 5, "message": "任务已取消"}
  ```

#### Scenario: Cancel non-existent task
- **WHEN** 请求取消不存在或已完成的任务
- **THEN** 返回 404 或 400 错误

---

### Requirement: Partial Failure Handling

系统 SHALL 在部分失败时继续执行剩余任务。

#### Scenario: Single item failure
- **WHEN** 批量任务中某一项失败（如某教授 Scholar 页面无法访问）
- **THEN** 记录失败原因
- **AND** 继续处理下一项
- **AND** 推送包含失败信息的进度事件

#### Scenario: Failure in progress event
- **WHEN** 某项处理失败
- **THEN** 进度事件包含失败信息：
  ```
  event: progress
  data: {"current": 6, "total": 20, "status": "running", "item": {"name": "Prof. Lee", "success": false, "error": "Scholar 页面无法访问"}}
  ```

#### Scenario: Final summary
- **WHEN** 任务完成
- **THEN** 完成事件包含成功/失败统计和失败详情

---

### Requirement: Batch Professor Crawl Task

系统 SHALL 支持批量爬取教授信息的异步任务。

#### Scenario: Start batch crawl
- **WHEN** POST `/api/tasks/batch-crawl` with `{ "scholar_urls": [...] }`
- **THEN** 创建批量爬取任务
- **AND** 返回 `{ "task_id": "uuid" }`

#### Scenario: Crawl progress
- **WHEN** 每爬取完成一位教授
- **THEN** 推送进度：教授姓名、机构、成功/失败状态

#### Scenario: Crawl completion
- **WHEN** 批量爬取完成
- **THEN** 成功的教授已保存到数据库
- **AND** 返回成功/失败数量和失败列表

---

### Requirement: Batch Letter Generation Task

系统 SHALL 支持批量生成邮件的异步任务。

#### Scenario: Start batch letter generation
- **WHEN** POST `/api/tasks/batch-letters` with `{ "professor_ids": [...], "language": "zh"|"en" }` 或 `{ "top": 5, "language": "zh"|"en" }`
- **THEN** 创建批量生成任务
- **AND** 返回 `{ "task_id": "uuid" }`

#### Scenario: Letter generation progress
- **WHEN** 每生成完成一封邮件
- **THEN** 推送进度：教授姓名、成功/失败状态

#### Scenario: Letter generation completion
- **WHEN** 批量生成完成
- **THEN** 成功的邮件已保存到数据库
- **AND** 返回成功/失败数量

---

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

### Requirement: Professor enrichment task progress granularity

系统 SHALL 为 `professor-enrichment` 任务提供与「计划执行的子步」一致的进度计数。

#### Scenario: Total reflects planned sub-steps
- **WHEN** 创建 `professor-enrichment` 任务
- **THEN** `total` 等于针对该教授、按用户设置计算得到的计划子步数（可为 1、2 或 3，或为 0 时不创建任务）

#### Scenario: Current advances per sub-step
- **WHEN** 任务运行中每完成一个已启用且实际执行的子步（出版物详情填充、论文摘要、科研画像）
- **THEN** `current` 递增 1
- **AND** 状态持久化以便 SSE 与任务列表读取一致

#### Scenario: Zero planned sub-steps in worker
- **WHEN** Worker 执行时发现计划子步数为 0
- **THEN** 任务标记为已完成并附带说明性 `message`，不执行 LLM 或爬虫子步

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

