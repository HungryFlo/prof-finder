# 实现任务清单

## 1. 后端：任务系统重构

- [x] 1.1 创建 `task_manager.py`：扩展 `TaskState`（`task_type`、`task_name`、`user_id`、`error_message`）
- [x] 1.2 重构 `GET /api/tasks/{task_id}/progress`：
  - [x] 移除内联任务执行逻辑
  - [x] 改为每 500ms 轮询 `task.status`，推送 `progress` 事件
  - [x] 任务完成/失败/取消时推送对应事件并结束 SSE 流
- [x] 1.3 将批量爬取执行逻辑抽取为独立协程 `execute_batch_crawl(task, scholar_urls)`
- [x] 1.4 将批量邮件生成执行逻辑抽取为独立协程 `execute_batch_letters(task, professor_ids, profile_id, api_key)`
- [x] 1.5 `POST /api/tasks/batch-crawl`：改为调用 `asyncio.create_task(execute_batch_crawl(...))`
- [x] 1.6 `POST /api/tasks/batch-letters`：改为调用 `asyncio.create_task(execute_batch_letters(...))`
- [x] 1.7 新增 `GET /api/tasks`：返回当前用户 `PENDING`/`RUNNING`/`FAILED` 状态的任务列表

## 2. 后端：单操作改为异步任务

- [x] 2.1 新增 `execute_single_crawl(task, scholar_url)` 协程
- [x] 2.2 重构 `POST /api/professors/scholar`：
  - [x] 创建 task（`task_type="single-crawl"`，`task_name="爬取教授"`, `total=1`）
  - [x] 调用 `asyncio.create_task(execute_single_crawl(...))`
  - [x] 返回 `{task_id, message}` 替代原有教授数据
- [x] 2.3 新增 `execute_match(task, profile_id)` 协程
- [x] 2.4 重构 `POST /api/match/run`：
  - [x] 创建 task（`task_type="match"`，`task_name="运行匹配算法"`，`total` 为教授总数）
  - [x] 调用 `asyncio.create_task(execute_match(...))`
  - [x] 返回 `{task_id, message}` 替代原有匹配结果
- [x] 2.5 新增 `execute_single_letter(task, professor_id, profile_id, api_key)` 协程
- [x] 2.6 重构 `POST /api/letters/generate/{professor_id}`：
  - [x] 创建 task（`task_type="single-letter"`，`task_name="生成邮件 [教授名]"`，`total=1`）
  - [x] 调用 `asyncio.create_task(execute_single_letter(...))`
  - [x] 返回 `{task_id, message}` 替代原有邮件内容
- [x] 2.7 `deps.py` 新增 `get_current_user_sse`：支持 `?token=` query param（EventSource 不支持自定义 Header）

## 3. 前端：Task Store

- [x] 3.1 定义 `TaskEntry` 接口（`taskId`, `taskType`, `taskName`, `status`, `current`, `total`, `message`, `errorMessage`, `eventSource`）
- [x] 3.2 在 `frontend/src/types/index.ts` 补充 `TaskListItem` 类型（对应 `GET /api/tasks` 响应）
- [x] 3.3 创建 `frontend/src/stores/tasks.ts`（Pinia store）：
  - [x] `activeTasks: Map<string, TaskEntry>` 状态
  - [x] `addTask(taskId, taskType, taskName, total, onComplete?)` action：建立 EventSource、监听事件、更新状态
  - [x] `removeTask(taskId)` action：关闭 EventSource、移除条目
  - [x] `restoreFromServer()` action：调用 `GET /api/tasks`，对活跃任务调用 `addTask()`
  - [x] EventSource 事件处理：`progress` 更新进度；`complete` 调用 onComplete 后自动 removeTask；`failed` 更新状态保留条目；`cancelled` 自动 removeTask
- [x] 3.4 在 `frontend/src/stores/index.ts` 导出 `useTaskStore`
- [x] 3.5 更新 `frontend/src/api/tasks.ts`：新增 `listTasks()` 方法，`getProgressUrl()` 接受 token 参数

## 4. 前端：TaskPanel 组件

- [x] 4.1 创建 `frontend/src/components/TaskPanel.vue`：
  - [x] 图标按钮（`NButton` + `NIcon`），有运行中任务时图标脉冲动画，有失败任务时 badge 红色显示
  - [x] `NPopover` 下拉面板（`placement="bottom-end"`）
  - [x] 任务列表，每项展示：任务名、进度文字（`X/Y` 或 `运行中...`）、状态图标
  - [x] 失败任务额外显示：错误信息（截断至 80 字符）+ X 关闭按钮
  - [x] 列表为空时显示"暂无运行中的任务"
- [x] 4.2 在 `MainLayout.vue` 的 Header 中引入 `TaskPanel`，放在用户头像左侧，`onMounted` 时调用 `restoreFromServer()`

## 5. 前端：页面迁移

- [x] 5.1 `ProfessorListView.vue`（单个教授爬取）：
  - [x] Scholar 链接添加改为调用 `POST /api/professors/scholar` 拿 task_id
  - [x] 调用 `tasksStore.addTask()`，`onComplete` 回调中刷新教授列表
- [x] 5.2 `MatchResultsView.vue`（运行匹配 + 生成邮件）：
  - [x] 运行匹配改为调用 `POST /api/match/run` 拿 task_id
  - [x] 生成邮件改为调用 `POST /api/letters/generate/{professor_id}` 拿 task_id
  - [x] 两者均调用 `tasksStore.addTask()` 并在 `onComplete` 中刷新列表
- [x] 5.3 `LetterListView.vue`（生成单封邮件）：
  - [x] 生成邮件改为调用 `POST /api/letters/generate/{professor_id}` 拿 task_id
  - [x] 调用 `tasksStore.addTask()`，`onComplete` 回调中刷新邮件列表

## 6. 前端：初始化恢复

- [x] 6.1 在 `MainLayout.vue` 的 `onMounted` 中调用 `tasksStore.restoreFromServer()` 恢复任务
