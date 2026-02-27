# Change: Add Background Task Panel

## Why

系统中的长任务（爬取教授、运行匹配、生成邮件）存在两个问题：
1. 批量任务依赖 SSE 连接内联执行，连接一旦断开（用户切换页面）任务即停止
2. 单次操作（单个教授爬取、运行匹配、生成单封邮件）完全同步阻塞，用户只能等待

用户无法在任务运行期间切换页面，也没有统一的任务进度视图。

## What Changes

### 后端
- 将任务执行从 SSE handler 内联迁移到 `asyncio.create_task()` 真正后台协程，SSE 端点改为纯进度轮询器
- 将以下三个同步端点改为异步任务模式，返回 `task_id` 而非直接结果：
  - `POST /api/professors/scholar`（单个教授爬取）
  - `POST /api/match/run`（运行匹配算法）
  - `POST /api/letters/generate/{professor_id}`（生成单封邮件）
- `TaskState` 新增 `task_type` 和 `task_name` 字段
- 新增 `GET /api/tasks` 端点，列出当前用户的活跃/近期任务（用于页面刷新后恢复）

### 前端
- 新增 `stores/tasks.ts`（Pinia store），统一管理所有活跃任务的 EventSource 连接和状态
- 新增 `components/TaskPanel.vue`，嵌入 Header 右侧：图标 + 下拉列表展示任务进度
- 各触发操作的页面改为调用 task store（而非等待 API 直接返回结果）：
  - `ProfessorListView.vue`
  - `MatchResultsView.vue`
  - `LetterListView.vue`
- 应用初始化时调用 `GET /api/tasks` 恢复已有任务

## Impact

- Affected specs: `task-panel`（新建）
- Affected code:
  - `backend/prof_finder/api/routes/tasks.py`
  - `backend/prof_finder/api/routes/professors.py`
  - `backend/prof_finder/api/routes/match.py`
  - `backend/prof_finder/api/routes/letters.py`
  - `frontend/src/stores/tasks.ts`（新建）
  - `frontend/src/stores/index.ts`
  - `frontend/src/components/TaskPanel.vue`（新建）
  - `frontend/src/layouts/MainLayout.vue`
  - `frontend/src/views/professor/ProfessorListView.vue`
  - `frontend/src/views/match/MatchResultsView.vue`
  - `frontend/src/views/letter/LetterListView.vue`
  - `frontend/src/types/index.ts`
  - `frontend/src/api/tasks.ts`
- **BREAKING**: `POST /api/professors/scholar`、`POST /api/match/run`、`POST /api/letters/generate/{professor_id}` 响应体从原始数据改为 `{task_id, message}`
