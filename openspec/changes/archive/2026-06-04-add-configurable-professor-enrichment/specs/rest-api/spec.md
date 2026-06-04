## MODIFIED Requirements

### Requirement: Settings API

系统 SHALL 提供用户设置的 REST API。

#### Scenario: Get settings
- **WHEN** GET `/api/settings`
- **THEN** 返回当前用户的设置
- **AND** API Key 以脱敏形式返回（仅显示前4位和后4位）

#### Scenario: Update settings
- **WHEN** PUT `/api/settings` with JSON body
- **THEN** 更新用户设置

#### Scenario: Settings fields
- **WHEN** 更新设置
- **THEN** 支持以下字段：
  - `deepseek_api_key`: DeepSeek API Key
  - `deepseek_base_url`: API Base URL
  - `request_delay`: 爬虫请求延时（秒）
  - `auto_enrich_on_save_fetch_publication_details`: 是否自动执行出版物详情拉取子步
  - `auto_enrich_on_save_paper_summaries`: 是否自动执行论文摘要子步
  - `auto_enrich_on_save_research_profile`: 是否自动执行科研画像子步

---

## ADDED Requirements

### Requirement: Professor auto-enrichment task metadata on write

当接口在写入或 Scholar 同步后启动 `professor-enrichment` 任务时，系统 SHALL 在响应中同时提供任务总子步数，供客户端进度条使用。

#### Scenario: Manual create returns total when task starts
- **WHEN** POST 手动创建教授 **且** 根据用户设置将执行至少一个自动 enrichment 子步
- **THEN** 响应包含 `enrichment_task_id`
- **AND** 响应包含 `enrichment_task_total`，其值等于该任务计划的子步数

#### Scenario: No task when all sub-steps disabled or planned count zero
- **WHEN** 用户关闭所有自动 enrichment 子步 **或** 按规则计算出计划子步数为 0
- **THEN** 响应不包含 `enrichment_task_id`（或为空）
- **AND** 不包含 `enrichment_task_total`（或为空）

#### Scenario: Scholar refresh returns total when task starts
- **WHEN** POST 刷新单个教授 Scholar **且** 启动自动 enrichment
- **THEN** 响应同时包含 `enrichment_task_id` 与 `enrichment_task_total`
