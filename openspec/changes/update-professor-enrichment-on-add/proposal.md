# Change: 教授添加时自动 enrichment

## Why

当前从 Scholar / 院校爬虫添加教授后，`paper_summaries` 与 `research_profile` 多为空，匹配阶段缺少高质量文本；Scholar 刷新还会清空全部 `paper_summaries`，与「丰富匹配信号」目标相反。

## What Changes

- 在 Scholar 单次/批量爬取、院校爬虫入库、手动创建教授、以及 Scholar 同步刷新完成后，自动串联：可选填充前 N 篇出版物的摘要页（`fill_publication`）、英文 LLM 论文摘要写入 `paper_summaries`（`source_type: scholar_pub`）、科研画像生成并失效 embedding。
- Scholar 刷新时仅移除 `scholar_pub` 类摘要，保留 PDF/ArXiv 来源摘要；刷新后触发上述 enrichment。
- 配置项 `PROFESSOR_ENRICHMENT_MAX_PUBLICATIONS`（默认 15）限制每位教授自动摘要数量。
- CLI `professor add` / `professor update` 在保存后同步运行同一套 pipeline（阻塞至完成）。

## Impact

- Affected specs: `data-model`, `professor-crawler`, `professor-profile`, `rest-api`, `professor-matching`, `cli`
- Affected code: `backend/prof_finder/config.py`, `source_input_service.py`, `task_manager.py`, `routes/professors.py`, `cli/professor.py`, frontend `TaskType`, i18n/task store（可选）
