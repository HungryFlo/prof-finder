## ADDED Requirements

### Requirement: Post-import professor enrichment

系统 SHALL 在通过 Google Scholar 或院校爬虫将教授写入当前用户教授池后，自动触发教授 enrichment pipeline（填充部分出版物正文、生成英文 `paper_summaries`、生成科研画像），除非该次写入被用户或系统明确跳过（本变更不提供跳过开关时，一律执行）。

#### Scenario: After single Scholar crawl task
- **WHEN** `single-crawl` 任务成功创建一名新教授
- **THEN** 系统 SHALL 启动后台 enrichment 任务并获得可订阅的 task 记录

#### Scenario: After batch Scholar crawl
- **WHEN** `batch-crawl` 任务完成且至少新增一名教授
- **THEN** 系统 SHALL 启动批量 enrichment 任务，顺序处理每位新增教授 ID

#### Scenario: After university department crawl
- **WHEN** `university-crawl` 任务完成且至少新增一名教授
- **THEN** 系统 SHALL 启动批量 enrichment 任务，顺序处理每位新增教授 ID
- **AND** 对无 Google Scholar 的教授，pipeline SHALL 仅执行可行步骤（如基于已有字段生成科研画像，不虚构 Scholar 论文摘要）

#### Scenario: Controlled concurrency
- **WHEN** 批量导入产生多名新教授
- **THEN** enrichment SHALL 在同一批量任务内顺序执行每位教授的处理，避免无上限并发 LLM 调用
