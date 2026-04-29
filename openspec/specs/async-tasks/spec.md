# async-tasks Specification

## Purpose
TBD - created by archiving change add-vue-web-frontend. Update Purpose after archive.
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
- **WHEN** POST `/api/tasks/batch-letters` with `{ "professor_ids": [...] }` 或 `{ "top": 5 }`
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

系统 SHALL 在内存中管理任务状态（不持久化）。

#### Scenario: Task lifecycle
- **WHEN** 任务创建
- **THEN** 任务状态保存在内存中
- **AND** 任务完成或取消后，状态在一定时间后清理（如 5 分钟）

#### Scenario: Server restart
- **WHEN** 服务器重启
- **THEN** 所有进行中的任务丢失
- **AND** 已保存到数据库的结果不受影响

#### Scenario: Task not found
- **WHEN** 请求不存在的 task_id
- **THEN** 返回 404 错误

