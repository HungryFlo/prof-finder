# Design: Background Task Panel

## Context

当前任务执行架构存在根本性缺陷：任务代码嵌在 SSE generator 函数内，FastAPI 的 `EventSourceResponse` 会在 SSE 连接断开时中止 generator，导致任务同时停止。

系统是单用户/个人部署（SQLite + 单进程 FastAPI），无需引入 Celery/Redis 等重型任务队列，用 `asyncio.create_task()` 即可满足需求。

## Goals / Non-Goals

- Goals:
  - 任务在 asyncio event loop 中后台运行，与 SSE 连接生命周期解耦
  - 前端有统一的任务进度面板，切换页面不丢失进度
  - 页面刷新后能恢复后端仍在运行的任务
  - 失败任务保留在列表，需手动关闭；成功任务自动消失
- Non-Goals:
  - 服务重启后任务持久化（内存存储足够个人使用场景）
  - 多 worker 并发（单进程 asyncio）
  - 任务优先级或依赖关系

## Architecture

### 后端：任务生命周期

```
POST /api/professors/scholar
  └─ create_task(total=1, type="single-crawl", name="爬取教授 xxx")
  └─ asyncio.create_task(execute_single_crawl(task, context))  ← 真正后台
  └─ return {task_id, message}

GET /api/tasks/{task_id}/progress  (SSE)
  └─ event_generator(): 每 500ms 轮询 task.status
      ├─ yield progress event (status=running)
      ├─ on COMPLETED → yield complete event, break
      ├─ on FAILED → yield failed event, break
      └─ on CANCELLED → yield cancelled event, break
```

各任务类型的 execute_xxx() 函数只做业务逻辑，通过修改 `task.status / current / message` 推进状态，不负责 SSE 通信。

### 后端：新增字段与端点

**TaskState 新增字段：**
```python
task_type: str           # "batch-crawl" | "batch-letters" | "single-crawl" | "match" | "single-letter"
task_name: str           # 人类可读名称，如 "批量爬取 5 个教授"
user_id: int             # 归属用户（从 context 提升到 TaskState）
error_message: str = ""  # 失败时的错误信息
```

**新增端点：**
```
GET /api/tasks
  → 返回当前用户所有 PENDING/RUNNING/FAILED 任务的列表
  → 仅返回 1 小时内创建的任务（防止长期堆积）
  → 用于页面刷新后前端恢复任务列表
```

### 前端：task store

```typescript
// stores/tasks.ts
interface TaskEntry {
  taskId: string
  taskType: 'batch-crawl' | 'batch-letters' | 'single-crawl' | 'match' | 'single-letter'
  taskName: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  current: number
  total: number
  message: string
  errorMessage?: string
  eventSource?: EventSource
}

// store actions
addTask(taskId, taskType, taskName, total): void
  → 创建 TaskEntry，建立 EventSource 连接，监听 progress/complete/failed/cancelled 事件

removeTask(taskId): void
  → 关闭 EventSource，从 store 移除

restoreFromServer(): Promise<void>  (应用初始化时调用)
  → GET /api/tasks → 对每个活跃任务调用 addTask()
```

### 前端：TaskPanel 组件

位置：`MainLayout.vue` 的 Header 右侧，用户头像左边。

```
[图标按钮]  ← NButton + NBadge（显示 running 任务数）
    │
    └─ NDropdown (placement="bottom-end")
         │
         └─ 任务列表（最大高度 400px，可滚动）
              ├─ [运行中] spinner + 任务名 + "X/Y" 或 "运行中..."
              └─ [失败]   错误图标 + 任务名 + 截断的错误信息 + X 关闭按钮
```

- 无任务时：图标正常显示，无 badge
- 有运行中任务：图标显示旋转动画（或 badge 显示数量）
- 有失败任务：badge 显示失败数量（用红色）

### 前端：各页面改造

原来等待同步结果的流程改为：
```
点击"添加教授" → POST /api/professors/scholar → 拿到 task_id
→ tasksStore.addTask(task_id, 'single-crawl', '爬取教授', 1)
→ 关闭 Modal，正常跳转，任务面板自动追踪进度
```

各页面不再 await 操作结果，但需要在任务完成后刷新数据：
- task store 的 `complete` 事件可以携带回调或触发全局事件（用 `mitt` 或直接在 store 中暴露回调钩子）
- 推荐：store 的 `addTask` 接受可选的 `onComplete` 回调，完成后调用

## Decisions

| 决策 | 选择 | 备选方案 | 理由 |
|------|------|------|------|
| 后台执行机制 | `asyncio.create_task()` | Celery, FastAPI BackgroundTasks | 单进程个人工具，asyncio 足够；BackgroundTasks 无法取消 |
| SSE 轮询间隔 | 500ms | 100ms / 1s | 100ms 太频繁；1s 延迟明显；500ms 体感流畅 |
| 单操作包装 | 也包装为 task | 保持同步返回 | 统一进度面板体验，用户操作一致 |
| 失败任务处理 | 保留 + 手动关闭 | 自动消失 / 弹 toast | 用户需要看到错误信息，不打断其他操作 |
| 页面刷新恢复 | GET /api/tasks | localStorage 记录 task_id | 后端是事实来源，localStorage 可能与后端不一致 |
| 完成后刷新数据 | onComplete 回调 | 全局事件总线 | 简单直接，无需引入额外依赖 |

## Risks / Trade-offs

- **asyncio 任务无法跨进程**：服务重启后所有进行中任务丢失。对个人部署可接受。
- **内存泄漏风险**：cleanup_old_tasks() 现有逻辑仅清理 5 分钟前已完成任务，需确保 asyncio task 本身也能被 GC
- **并发写入 TaskState**：asyncio 单线程，但需注意 `session` 不能跨 await 复用（每次操作重新获取 session）

## Migration Plan

1. 后端改造（不影响已有批量端点的外部行为，仅改执行方式）
2. 三个破坏性端点的响应格式变更，前端同步更新
3. 前端新增 task store 和 TaskPanel
4. 各页面迁移到异步模式
