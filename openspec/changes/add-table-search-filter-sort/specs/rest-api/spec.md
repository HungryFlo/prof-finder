## MODIFIED Requirements
### Requirement: Professor API

系统 SHALL 提供教授管理的 REST API。

#### Scenario: List professors
- **WHEN** GET `/api/professors`
- **THEN** 返回当前用户的教授列表
- **AND** 支持分页参数 `?page=1&page_size=20`
- **AND** 支持筛选参数 `?affiliation=xxx&interest=xxx`
- **AND** 支持搜索参数 `?search=xxx`（按姓名和机构模糊匹配）
- **AND** 支持排序参数 `?sort_by=name|affiliation|h_index|updated_at&sort_order=asc|desc`

#### Scenario: List affiliations
- **WHEN** GET `/api/professors/affiliations`
- **THEN** 返回当前用户所有教授的去重机构列表
- **AND** 排除空值

#### Scenario: Add professor manually
- **WHEN** POST `/api/professors` with JSON body
- **THEN** 创建教授记录并返回

#### Scenario: Add professor by Scholar link
- **WHEN** POST `/api/professors/scholar` with `{ "url": "..." }`
- **THEN** 爬取 Google Scholar 信息
- **AND** 创建教授记录并返回

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

#### Scenario: Batch delete professors
- **WHEN** DELETE `/api/professors/batch` with `{ "ids": [...] }`
- **THEN** 删除所有指定的教授

---

### Requirement: Match API

系统 SHALL 提供匹配功能的 REST API。

#### Scenario: Run matching
- **WHEN** POST `/api/match/run`
- **AND** 存在激活的简历和教授数据
- **THEN** 执行匹配算法
- **AND** 保存匹配结果
- **AND** 返回匹配结果列表

#### Scenario: Get match results
- **WHEN** GET `/api/match/results`
- **THEN** 返回当前激活简历的匹配结果
- **AND** 支持分页参数 `?page=1&page_size=20`
- **AND** 支持筛选参数 `?min_score=70`
- **AND** 支持搜索参数 `?search=xxx`（按教授姓名模糊匹配）
- **AND** 支持排序参数 `?sort_by=score|professor_name|professor_affiliation&sort_order=asc|desc`
- **AND** 默认按匹配分数降序排列

#### Scenario: Get single match detail
- **WHEN** GET `/api/match/results/{professor_id}`
- **THEN** 返回与该教授的匹配详情
- **AND** 包含匹配原因分析

#### Scenario: No active profile
- **WHEN** POST `/api/match/run`
- **AND** 没有激活的简历
- **THEN** 返回错误：请先激活一份简历

#### Scenario: No professors
- **WHEN** POST `/api/match/run`
- **AND** 没有教授数据
- **THEN** 返回错误：请先添加教授
