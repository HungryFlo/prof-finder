## MODIFIED Requirements

### Requirement: Professor API

系统 SHALL 提供教授管理的 REST API。

#### Scenario: List professors
- **WHEN** GET `/api/professors`
- **THEN** 返回当前用户的教授列表
- **AND** 支持分页参数 `?page=1&page_size=20`
- **AND** 支持筛选参数 `?affiliation=xxx&interest=xxx`

#### Scenario: Add professor manually
- **WHEN** POST `/api/professors` with JSON body
- **THEN** 创建教授记录并返回
- **AND** 系统 SHALL 自动启动后台 enrichment 任务（至少包含科研画像生成；若无 Scholar 出版物则无 Scholar 衍生摘要）

#### Scenario: Add professor by Scholar link
- **WHEN** POST `/api/professors/scholar` with `{ "url": "..." }`
- **THEN** 爬取 Google Scholar 信息
- **AND** 创建教授记录并通过任务面板返回任务 ID
- **AND** 爬取成功入库后 SHALL 自动启动 enrichment 任务

#### Scenario: Search Scholar
- **WHEN** POST `/api/professors/search` with `{ "query": "..." }`
- **THEN** 搜索 Google Scholar
- **AND** 返回搜索结果列表（不自动添加）

#### Scenario: Get professor detail
- **WHEN** GET `/api/professors/{id}`
- **THEN** 返回教授详情（含论文列表）

#### Scenario: Update professor
- **WHEN** PUT `/api/professors/{id}` with JSON body
- **THEN** 更新教授信息

#### Scenario: Delete professor
- **WHEN** DELETE `/api/professors/{id}`
- **THEN** 删除教授记录

#### Scenario: Refresh professor data
- **WHEN** POST `/api/professors/{id}/refresh`
- **AND** 教授有 Google Scholar 链接
- **THEN** 重新爬取数据并更新
- **AND** SHALL 保留非 Scholar 自动来源的 `paper_summaries` 条目
- **AND** 更新完成后 SHALL 启动 enrichment 任务以重建 Scholar 衍生摘要与科研画像

#### Scenario: Batch delete professors
- **WHEN** DELETE `/api/professors/batch` with `{ "ids": [...] }`
- **THEN** 删除所有指定的教授
