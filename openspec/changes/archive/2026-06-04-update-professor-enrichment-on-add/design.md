## Context

教授池数据需在添加后尽快具备 `paper_summaries`（英文）与 `research_profile`，供语义匹配与邮件生成使用。现有逻辑依赖用户手动触发总结任务或画像任务。

## Goals / Non-Goals

- Goals: 单一可观测后台任务类型展示 enrichment 进度；控制 Scholar 请求与 LLM 调用量；与现 `SourceInput` 摘要共存。
- Non-Goals: 不引入分布式队列；不改变 `paper_summarizer` 模板结构；院校爬虫不自动补 Scholar。

## Decisions

1. **任务形状**: 单次添加或刷新后启动 `professor-enrichment`；批量爬取（batch-crawl / university-crawl）在全部入库结束后启动 **一个** `batch-professor-enrichment` 任务，顺序处理每位新增教授 ID，避免大量并发 LLM。
2. **上限 N**: `Settings.professor_enrichment_max_publications`，环境变量 `PROFESSOR_ENRICHMENT_MAX_PUBLICATIONS`，默认 15；仅对 `publications` 列表前 N 条尝试 `fill_publication` 与摘要。
3. **无 `author_pub_id` 的出版物**: 仍生成一条 `scholar_pub` 摘要，正文为 `abstract` 或空字符串，由现有 `PaperSummarizer` 与 prompt 处理信息不足情况。
4. **刷新**: `paper_summaries` 中 `source_type == scholar_pub` 的条目在 Scholar 数据重写前删除；非 `scholar_pub` 条目保留。成功后异步跑完整 enrichment（可再次生成 scholar_pub 摘要与更新画像）。
5. **失败**: 某篇 `fill_publication` 或单次 LLM 失败不中止整条 pipeline（记录 internal results / task.failed_count 可后续增强）；画像阶段失败则任务 FAILED。

## Risks / Trade-offs

- 批量导入时 enrichment 单任务耗时变长 → 接受，以控制并发与 API 费用。
- CLI 同步阻塞 → 文档化；教学场景可接受。

## Migration Plan

- 无需 DB migration；新摘要字段均为 JSON 内新对象 shape。
