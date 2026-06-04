## ADDED Requirements

### Requirement: DBLP professor API

系统 SHALL 通过 DBLP 官方 API 补充教授档案，并与 Google Scholar 数据合并存储。

#### Scenario: Search DBLP authors

- **WHEN** POST `/api/professors/dblp/search` with `{ "query": "...", "limit": N }`
- **THEN** 调用 DBLP author search API
- **AND** 返回作者列表（name、pid、url、affiliations）

#### Scenario: Add professor by DBLP URL

- **WHEN** POST `/api/professors/dblp` with `{ "url": "https://dblp.org/pid/..." }`
- **THEN** 启动 `single-dblp-crawl` 任务
- **AND** 将 DBLP 论文合并入 `publications`（`source=dblp`）

#### Scenario: Match external profiles

- **WHEN** POST `/api/professors/{id}/match-external`
- **THEN** 对未关联 Scholar 的教授启动 Scholar 匹配任务
- **AND** 对未关联 DBLP 的教授启动 DBLP 匹配任务

#### Scenario: Refresh external data in batch

- **WHEN** POST `/api/professors/batch-refresh-external` with professor ids
- **THEN** 按教授已有链接分别刷新 Scholar 与 DBLP 源数据
- **AND** 分源更新 `publications`，互不覆盖另一数据源条目
