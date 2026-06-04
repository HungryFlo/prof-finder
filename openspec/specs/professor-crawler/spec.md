# professor-crawler Specification

## Purpose

定义教授信息获取：Google Scholar、DBLP、院校站点爬虫注册表及批量导入流程，包含请求延时、去重与后台任务集成；用户须遵守各数据源服务条款与 robots 约定。
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

