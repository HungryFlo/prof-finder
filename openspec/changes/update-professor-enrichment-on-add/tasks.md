## 1. OpenSpec（阶段 1）

- [x] 1.1 创建 `proposal.md` / `design.md` / 各能力 `specs/*/spec.md` delta
- [x] 1.2 `openspec validate update-professor-enrichment-on-add --strict --no-interactive`

## 2. 实现（阶段 2）

- [x] 2.1 `Settings` 增加 `professor_enrichment_max_publications`
- [x] 2.2 `source_input_service`：`keep_non_scholar_paper_summaries`、`build_paper_summary_from_scholar_publication`
- [x] 2.3 `task_manager`：`execute_professor_enrichment`、`execute_batch_professor_enrichment`；`single-crawl` / `batch-crawl` / `university-crawl` / `batch-refresh` 接线；刷新路径改为 strip scholar_pub
- [x] 2.4 `routes/professors.py`：`create_professor`、`refresh` 异步调度 enrichment
- [x] 2.5 `cli/professor.py`：`add` / `_update_professor_from_scholar` 后 `asyncio.run` pipeline
- [x] 2.6 前端 `TaskType` + task store 文案；pytest 覆盖 strip 与刷新不删 pdf 摘要（如能 mock）
