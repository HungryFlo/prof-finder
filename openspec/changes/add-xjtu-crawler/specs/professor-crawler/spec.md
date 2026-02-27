## ADDED Requirements

### Requirement: University Crawler Registry

系统 SHALL 维护一个已注册院校爬虫的注册表，并通过 API 向前端暴露可用爬虫列表。

#### Scenario: Query available crawlers

- **WHEN** 客户端请求 `GET /api/professors/university-crawlers`
- **THEN** 返回已注册爬虫列表，每项包含 `university_id` 和 `display_name`

#### Scenario: Unknown university_id rejected

- **WHEN** 客户端提交 `POST /api/professors/crawl-university` 且 `university_id` 不在注册表中
- **THEN** 返回 HTTP 400，提示"不支持该院校"

---

### Requirement: XJTU CS Department Crawl

系统 SHALL 支持爬取西安交通大学计算机科学与技术学院（`university_id: "xjtu-cs"`）的教授列表，作为后台长任务执行并通过 SSE 推送进度。

#### Scenario: Start crawl task

- **WHEN** 用户在前端选择"西安交通大学 - 计算机科学与技术学院"并确认
- **THEN** 系统创建后台任务并返回 `task_id`
- **AND** 前端通过现有 TaskPanel 订阅 SSE 进度

#### Scenario: Crawl completes successfully

- **WHEN** 爬取任务运行完毕
- **THEN** 每位教授保存至当前用户的教授池，字段包含 `name, affiliation, source_url`，以及可选的 `email, homepage, research_interests`
- **AND** 已存在（同 `name + affiliation`）的教授跳过，不重复导入

#### Scenario: Crawl with partial failures

- **WHEN** 某个教授详情页请求失败
- **THEN** 记录为失败项并继续爬取其余教授
- **AND** 任务最终标记为 COMPLETED，在结果中标注失败数量

---

### Requirement: University Crawler Error Handling

系统 SHALL 对院校爬取过程中的网络错误进行容错处理。

#### Scenario: List page unreachable

- **WHEN** 院校列表页请求失败（网络超时或非 200 响应）
- **THEN** 任务标记为 FAILED，`error_message` 包含具体错误原因

#### Scenario: Individual detail page fails

- **WHEN** 某位教授详情页请求异常
- **THEN** 该教授记录为失败，任务继续处理剩余教授
- **AND** 不影响整体任务完成状态
