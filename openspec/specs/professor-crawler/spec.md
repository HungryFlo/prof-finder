# professor-crawler Specification

## Purpose
TBD - created by archiving change add-xjtu-crawler. Update Purpose after archive.
## Requirements
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

### Requirement: XJTU SE Department Crawl

系统 SHALL 支持爬取西安交通大学软件学院（`university_id: "xjtu-se"`）的教师列表，作为后台长任务执行并通过 SSE 推送进度。

#### Scenario: Start SE crawl task

- **WHEN** 用户选择"西安交通大学 - 软件学院"并触发爬取
- **THEN** 系统创建后台任务并返回 `task_id`
- **AND** 前端通过现有 TaskPanel 订阅 SSE 进度

#### Scenario: List page parsed by category

- **WHEN** 爬取 `https://se.xjtu.edu.cn/jsdw.htm` 成功
- **THEN** 系统遍历所有 `div.teaSub` 分类，从 `ul.clearfix > li > a` 中提取教师姓名和详情页 URL

#### Scenario: Detail page fetched for each teacher

- **WHEN** 教师列表解析完成
- **THEN** 系统依次访问每位教师的 `gr.xjtu.edu.cn` 个人主页
- **AND** 从详情页提取邮箱、研究方向等字段（若存在）

#### Scenario: Crawl completes successfully

- **WHEN** 爬取任务运行完毕
- **THEN** 每位教师保存至当前用户的教授池，字段包含 `name, affiliation, source_url`，以及可选的 `email, homepage, research_interests`
- **AND** 已存在（同 `name + affiliation`）的教师跳过，不重复导入

#### Scenario: Teacher without detail link

- **WHEN** 列表页中某位教师的 `<a>` 标签无 `href` 属性
- **THEN** 该教师仍被导入，`source_url` 使用列表页 URL，`email` 和 `research_interests` 为空

#### Scenario: Detail page request fails

- **WHEN** 某位教师的详情页请求失败（网络超时、502 或解析异常）
- **THEN** 该教师降级保存（仅含列表页信息），记录为失败项并继续处理其余教师
- **AND** 任务最终标记为 COMPLETED，在结果中标注失败数量

