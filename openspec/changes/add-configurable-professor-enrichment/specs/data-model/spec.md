## ADDED Requirements

### Requirement: UserSettings auto-enrichment columns

`user_settings` 表 SHALL 持久化三个布尔列，用于控制写入或 Scholar 同步后的自动教授 enrichment 子步。

#### Scenario: New columns exist after migration
- **WHEN** 应用在已有数据库上启动并完成迁移
- **THEN** `user_settings` 包含 `auto_enrich_on_save_fetch_publication_details`、`auto_enrich_on_save_paper_summaries`、`auto_enrich_on_save_research_profile` 列
- **AND** 现有行的默认值为 true（与历史行为一致）
