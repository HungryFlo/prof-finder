## MODIFIED Requirements
### Requirement: Background Task Execution
系统 SHALL 将所有长任务（批量爬取、批量邮件生成、单个教授爬取、运行匹配、生成单封邮件、Web 简历解析）在 asyncio 后台协程中执行，执行生命周期与 SSE 连接解耦。

#### Scenario: 任务执行与 SSE 连接解耦
- **WHEN** 长任务启动后客户端断开 SSE 连接
- **THEN** 任务继续在后台运行直至完成或失败

#### Scenario: SSE 端点作为纯进度轮询器
- **WHEN** 客户端连接 `GET /api/tasks/{task_id}/progress`
- **THEN** 服务端每 500ms 推送一次当前进度，不执行任何业务逻辑

#### Scenario: Web 简历解析后台执行
- **WHEN** Web 用户上传简历并发起解析
- **THEN** 系统创建 `profile-parse` 后台任务并立即返回 `{task_id, message}`
- **AND** 任务在后台解析并保存简历

### Requirement: Frontend Task Panel
前端 SHALL 在 Header 右侧提供任务面板图标，点击展开当前任务进度列表，并以清晰分组展示运行中、失败、已完成任务。

#### Scenario: 运行中任务展示
- **WHEN** 有任务处于 `running` 或 `pending` 状态
- **THEN** 图标显示旋转动画，下拉列表中展示任务名和进度（批量任务显示 `X/Y`，单次任务显示当前消息或"运行中..."）

#### Scenario: 角标仅统计未完成任务
- **WHEN** 任务面板中同时存在未完成任务和 `completed` 任务
- **THEN** Header 图标角标仅统计 `pending`、`running`、`failed` 状态的任务数量
- **AND** `completed` 状态任务不计入角标数量

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

#### Scenario: 状态分组展示
- **WHEN** 任务面板中同时存在多种状态的任务
- **THEN** 面板按运行中、失败、已完成分组展示，并隐藏空分组

#### Scenario: 面板跨页面持久
- **WHEN** 用户在任务运行期间切换到其他页面
- **THEN** 任务面板仍显示在 Header 中，进度继续更新

## ADDED Requirements
### Requirement: Task Completion Notifications
前端 SHALL 在后台任务完成或失败时显示侧边通知，帮助用户在不打开任务面板时获知任务结果。

#### Scenario: 完成通知
- **WHEN** 任务状态通过 SSE 变为 `completed`
- **THEN** 前端显示成功通知，包含任务名称和完成说明

#### Scenario: 失败通知
- **WHEN** 任务状态通过 SSE 变为 `failed`
- **THEN** 前端显示失败通知，包含任务名称和错误信息

#### Scenario: 通知不移除任务
- **WHEN** 前端显示完成或失败通知
- **THEN** 任务仍保留在任务面板中，直到用户手动关闭或清空已完成任务
