## ADDED Requirements

### Requirement: Professor Profile Page Enrichment (crawl4ai)

系统 SHALL 使用 crawl4ai 抓取教师个人主页/详情页，并通过 LLM 提取结构化字段；写回时 SHALL 与已有教授数据合并，不丢弃已有信息。

#### Scenario: Generic list crawl enriches profile pages

- **WHEN** 用户通过 `generic-university-crawl` 完成列表页爬取且记录含 profile URL（`homepage` 或列表 `url`）
- **THEN** 系统依次访问各 profile URL 提取详情
- **AND** 将 email、research_interests、bio 等合并入待入库记录后再保存

#### Scenario: Manual homepage crawl from professor detail

- **WHEN** 用户对已设置 `homepage` 的教授调用 `POST /api/professors/{id}/crawl-homepage`
- **THEN** 系统创建 `professor-homepage-crawl` 后台任务并通过 SSE 推送进度
- **AND** 完成后将合并结果写回该教授记录

#### Scenario: Homepage URL missing for manual crawl

- **WHEN** 教授 `homepage` 为空时调用 `crawl-homepage`
- **THEN** 返回 HTTP 400，提示先填写个人主页 URL

#### Scenario: Profile page crawl fails for one professor

- **WHEN** 某位教师的详情页爬取或 LLM 提取失败
- **THEN** 保留列表页/已有字段，继续处理其余教师
- **AND** 批量任务不因单条失败而整体失败

#### Scenario: Merge preserves existing email

- **WHEN** 爬取得到的新 email 与已有 email 不同且已有值非空
- **THEN** 保留原有 email
- **AND** 将新 email 追加到 `manual_notes`（`爬取邮箱: ...`）

#### Scenario: Merge unions research interests

- **WHEN** 爬取得到新的研究方向
- **THEN** 与已有 `research_interests` 按顺序去重合并
