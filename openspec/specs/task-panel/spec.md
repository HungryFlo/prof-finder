# task-panel Specification

## Purpose
TBD - created by archiving change add-background-task-panel. Update Purpose after archive.
## Requirements
### Requirement: Background Task Execution
系统 SHALL 将所有长任务（批量爬取、批量邮件生成、单个教授爬取、运行匹配、生成单封邮件）在 asyncio 后台协程中执行，执行生命周期与 SSE 连接解耦。

#### Scenario: 任务执行与 SSE 连接解耦
- **WHEN** 长任务启动后客户端断开 SSE 连接
- **THEN** 任务继续在后台运行直至完成或失败

#### Scenario: SSE 端点作为纯进度轮询器
- **WHEN** 客户端连接 `GET /api/tasks/{task_id}/progress`
- **THEN** 服务端每 500ms 推送一次当前进度，不执行任何业务逻辑

### Requirement: Async Single Operations
以下操作 SHALL 改为异步任务模式，返回 `{task_id, message}` 而非直接结果：
- `POST /api/professors/scholar`（单个教授爬取）
- `POST /api/match/run`（运行匹配算法）
- `POST /api/letters/generate/{professor_id}`（生成单封邮件）

#### Scenario: 单个教授爬取异步化
- **WHEN** 调用 `POST /api/professors/scholar`
- **THEN** 返回 `{task_id, message}`，任务在后台执行爬取并写入数据库

#### Scenario: 运行匹配异步化
- **WHEN** 调用 `POST /api/match/run`
- **THEN** 返回 `{task_id, message}`，任务在后台执行匹配算法

#### Scenario: 生成单封邮件异步化
- **WHEN** 调用 `POST /api/letters/generate/{professor_id}`
- **THEN** 返回 `{task_id, message}`，任务在后台调用 LLM 并写入邮件内容

### Requirement: Task List Endpoint
系统 SHALL 提供 `GET /api/tasks` 端点，返回当前用户的活跃任务列表。

#### Scenario: 获取活跃任务列表
- **WHEN** 已登录用户调用 `GET /api/tasks`
- **THEN** 返回该用户所有 `PENDING`/`RUNNING`/`FAILED` 状态的任务，包含 `task_id`、`task_type`、`task_name`、`status`、`current`、`total`

#### Scenario: 任务归属隔离
- **WHEN** 用户 A 调用 `GET /api/tasks`
- **THEN** 仅返回用户 A 的任务，不包含其他用户的任务

### Requirement: Frontend Task Panel
前端 SHALL 在 Header 右侧提供任务面板图标，点击展开当前任务进度列表。

#### Scenario: 运行中任务展示
- **WHEN** 有任务处于 `running` 或 `pending` 状态
- **THEN** 图标显示旋转动画，下拉列表中展示任务名和进度（批量任务显示 `X/Y`，单次任务显示"运行中..."）

#### Scenario: 成功任务保留
- **WHEN** 任务状态变为 `completed`
- **THEN** 该任务保留在面板列表中，并显示完成状态

#### Scenario: 失败任务保留
- **WHEN** 任务状态变为 `failed`
- **THEN** 该任务留在面板列表中，显示错误信息和关闭按钮，不影响其他任务的执行和显示

#### Scenario: 手动关闭失败或完成任务
- **WHEN** 用户点击失败或完成任务的关闭按钮
- **THEN** 该任务从面板列表中移除

#### Scenario: 存在 completed 任务时清空按钮可见
- **WHEN** 任务面板中存在至少一个 `completed` 状态的任务
- **THEN** 面板头部显示「清空已完成」按钮

#### Scenario: 无 completed 任务时清空按钮隐藏
- **WHEN** 任务面板中没有任何 `completed` 状态的任务
- **THEN** 面板头部不显示「清空已完成」按钮

#### Scenario: 点击按钮批量清除
- **WHEN** 用户点击「清空已完成」按钮
- **THEN** 所有 `completed` 状态的任务从面板列表中移除，`pending`/`running`/`failed` 状态的任务不受影响

#### Scenario: 面板跨页面持久
- **WHEN** 用户在任务运行期间切换到其他页面
- **THEN** 任务面板仍显示在 Header 中，进度继续更新

### Requirement: Task State Recovery on Refresh
前端 SHALL 在页面加载后调用 `GET /api/tasks` 恢复仍在后端运行的任务。

#### Scenario: 页面刷新后恢复任务
- **WHEN** 用户刷新页面，后端仍有 `RUNNING` 任务
- **THEN** 前端重新建立对应任务的 SSE 连接，面板显示恢复的任务进度

#### Scenario: 无活跃任务时面板为空
- **WHEN** 用户刷新页面，后端无活跃任务
- **THEN** 面板显示"暂无运行中的任务"

