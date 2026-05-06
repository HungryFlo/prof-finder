## Context

自动 enrichment 核心为 `_enrich_professor_core` 内顺序三段：出版物详情填充（依赖 Scholar + 非空 `publications`）、`paper_summaries` LLM、`research_profile` LLM。用户设置三项布尔，默认全开。

## Decisions

- **planned 计数规则**：与代码分支一致——仅当「开启详情填充 **且** 存在 `google_scholar_id` **且** `publications` 非空」时计入第一子步；摘要/画像各自受开关约束，只要开关为真即计入（与当前实现对无论文教授仍可能跑后续步一致）。
- **单教授任务进度**：`create_task(..., total=planned)`；执行体内每完成一子步 `current += 1` 并 `persist_task`；`total` 在执行开始时如与 DB 不一致则以重算的 `planned` 覆盖（防御性）。
- **批量 `batch-professor-enrichment`**：外层 `current/total` 仍为教授个数；内层子步只更新 `message`，不修改外层 `current`。
- **零步行为**：路由层若 `planned==0` 则不创建任务；若 Worker 仍收到任务且 `planned==0`，立即 `COMPLETED` 并附带说明信息。

## Non-Goals

- 不改变用户手动触发的「生成科研画像」等独立任务类型。
- 不在本变更中修正 async-tasks 全局规范里「任务不持久化」与实现的差异。
