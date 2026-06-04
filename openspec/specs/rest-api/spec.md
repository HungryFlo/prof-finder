# rest-api Specification

## Purpose

定义面向 Vue 前端的 FastAPI REST 接口（学生画像、教授、匹配、邮件、设置、任务进度等），包括认证保护、分页/筛选约定及与 Huey 后台任务协作的异步操作契约。
## Requirements
### Requirement: Profile API

系统 SHALL 提供简历管理的 REST API。

#### Scenario: List profiles
- **WHEN** GET `/api/profiles`
- **THEN** 返回当前用户的所有简历列表

#### Scenario: Create profile manually
- **WHEN** POST `/api/profiles` with JSON body
- **THEN** 创建新简历并返回

#### Scenario: Upload profile file
- **WHEN** POST `/api/profiles/upload` with multipart form
- **AND** 文件为 .md 或 .tex 格式
- **THEN** 解析文件内容
- **AND** 返回解析结果（不自动保存，等待用户确认）

#### Scenario: Confirm and save uploaded profile
- **WHEN** POST `/api/profiles` with parsed data and `source: "upload"`
- **THEN** 保存简历到数据库

#### Scenario: Get profile detail
- **WHEN** GET `/api/profiles/{id}`
- **AND** 简历属于当前用户
- **THEN** 返回简历详情

#### Scenario: Update profile
- **WHEN** PUT `/api/profiles/{id}` with JSON body
- **AND** 简历属于当前用户
- **THEN** 更新简历并返回

#### Scenario: Delete profile
- **WHEN** DELETE `/api/profiles/{id}`
- **AND** 简历属于当前用户
- **THEN** 删除简历

#### Scenario: Activate profile
- **WHEN** POST `/api/profiles/{id}/activate`
- **THEN** 将该简历设为激活状态
- **AND** 其他简历设为非激活

#### Scenario: Batch delete profiles
- **WHEN** DELETE `/api/profiles/batch` with `{ "ids": [...] }`
- **THEN** 删除所有指定的简历（仅限当前用户的）

---

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

### Requirement: Letter API

系统 SHALL 提供邮件生成的 REST API。

#### Scenario: Generate letter
- **WHEN** POST `/api/letters/generate/{professor_id}`
- **AND** 存在匹配结果
- **THEN** 调用 LLM 生成邮件
- **AND** 保存并返回邮件内容

#### Scenario: Batch generate letters
- **WHEN** POST `/api/letters/batch` with `{ "top": 5 }`
- **THEN** 为 Top N 匹配的教授生成邮件
- **AND** 返回生成结果列表

#### Scenario: List letters
- **WHEN** GET `/api/letters`
- **THEN** 返回所有已生成的邮件列表

#### Scenario: Get letter detail
- **WHEN** GET `/api/letters/{professor_id}`
- **THEN** 返回邮件详情

#### Scenario: Update letter
- **WHEN** PUT `/api/letters/{professor_id}` with `{ "content": "..." }`
- **THEN** 更新邮件内容（用户编辑后保存）

#### Scenario: API key not configured
- **WHEN** 调用生成邮件接口
- **AND** 用户未配置 DeepSeek API Key
- **THEN** 返回错误：请先配置 API Key

---

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

### Requirement: API Response Format

系统 SHALL 使用统一的 API 响应格式。

#### Scenario: Success response
- **WHEN** API 调用成功
- **THEN** 返回：
  ```json
  {
    "data": { ... },
    "message": "操作成功"
  }
  ```

#### Scenario: Error response
- **WHEN** API 调用失败
- **THEN** 返回：
  ```json
  {
    "error": "错误类型",
    "detail": "详细错误信息"
  }
  ```
- **AND** 使用适当的 HTTP 状态码（400/401/403/404/500）

#### Scenario: Paginated response
- **WHEN** 返回分页数据
- **THEN** 返回：
  ```json
  {
    "data": {
      "items": [...],
      "total": 100,
      "page": 1,
      "page_size": 20,
      "pages": 5
    }
  }
  ```

### Requirement: Source Input API

系统 SHALL 提供可复用的来源输入 API，支持 PDF 与 ArXiv 链接处理，供教授编辑与未来个人信息编辑共用。

#### Scenario: Upload PDF source
- **WHEN** POST `/api/source-inputs/pdf` with multipart form
- **AND** 文件类型为 `application/pdf`
- **THEN** 创建 PDF 类型 SourceInput 记录
- **AND** 使用 `pymupdf4llm` 提取 Markdown 文本预览
- **AND** 返回 `source_input_id`、处理状态与提取预览（若可用）

#### Scenario: Reject invalid PDF
- **WHEN** 上传非 PDF 文件或文件损坏
- **THEN** 返回 400 错误并包含可读错误信息

#### Scenario: Submit ArXiv source
- **WHEN** POST `/api/source-inputs/arxiv` with `{ "url": "..." }`
- **THEN** 校验链接并规范化 ArXiv ID
- **AND** 通过 ArXiv 官方 API 拉取元数据与 PDF 下载地址
- **AND** 下载论文 PDF 并复用 `pymupdf4llm` 解析链路
- **AND** 创建 ArXiv 类型 SourceInput 记录
- **AND** 返回 `source_input_id` 与抓取到的元数据预览（若可用）

#### Scenario: Keep metadata when ArXiv PDF download fails
- **WHEN** 提交 ArXiv 链接后元数据获取成功
- **AND** PDF 下载或解析失败
- **THEN** 接口仍返回成功创建的 `source_input_id` 与元数据预览
- **AND** 返回状态指示该记录为“仅元数据”
- **AND** 返回可读提示，指导用户稍后重试 PDF 解析

#### Scenario: Retry ArXiv PDF parsing
- **WHEN** POST `/api/source-inputs/{id}/retry-pdf-parse`
- **AND** 该记录为 ArXiv 且当前为仅元数据状态
- **THEN** 系统重新尝试下载 PDF 并走 `pymupdf4llm` 解析
- **AND** 成功后更新提取结果与状态

#### Scenario: ArXiv PDF download fails with metadata fallback
- **WHEN** 调用 POST `/api/source-inputs/arxiv`
- **AND** 元数据拉取成功但 PDF 下载失败
- **THEN** 接口返回成功并包含 `metadata_only=true`
- **AND** 返回可读提示，告知用户稍后可重试 PDF 解析
- **AND** SourceInput 记录中保留失败原因

#### Scenario: Retry PDF parse for metadata-only source
- **WHEN** POST `/api/source-inputs/{id}/retry-pdf-parse`
- **AND** 该来源为 `arxiv` 且 `metadata_only=true`
- **THEN** 系统重试下载 PDF 并执行 `pymupdf4llm` 解析
- **AND** 成功后更新 `metadata_only=false` 并写入提取结果

#### Scenario: Get source input detail
- **WHEN** GET `/api/source-inputs/{id}`
- **AND** 记录属于当前用户
- **THEN** 返回来源输入详情、状态与错误信息

#### Scenario: Cleanup temporary file after parse
- **WHEN** PDF 解析流程完成
- **THEN** 系统删除 ArXiv 下载的临时 PDF 文件
- **AND** 接口响应不暴露本地临时路径

#### Scenario: User-isolated source inputs
- **WHEN** 用户访问不属于自己的 SourceInput
- **THEN** 返回 404 或 403，且不泄露资源存在性细节

---

### Requirement: Professor Edit Enrichment API

系统 SHALL 提供教授编辑增强 API，支持手动编辑与来源输入（PDF/ArXiv）协同更新。

#### Scenario: Preview professor updates
- **WHEN** POST `/api/professors/{id}/edit-preview` with payload:
  - `manual_patch`（手动编辑字段，可选）
  - `source_input_ids`（来源输入列表，可选）
- **THEN** 返回“候选变更”结果
- **AND** 不直接写入教授主记录

#### Scenario: Confirm professor updates
- **WHEN** POST `/api/professors/{id}/apply-edits` with confirmed payload
- **THEN** 应用确认后的字段更新
- **AND** 记录本次更新使用的 `source_input_ids`
- **AND** 将来源输入沉淀为 `paper_summaries`（若可提取）
- **AND** 返回更新后的教授详情

#### Scenario: LLM summarization prompt managed centrally
- **WHEN** 系统执行论文总结
- **THEN** 使用 `backend/prof_finder/prompts/` 目录中的统一 prompt 模板
- **AND** 不在业务路由中硬编码 prompt 文本

#### Scenario: Include paper summaries in professor detail
- **WHEN** GET `/api/professors/{id}`
- **THEN** 返回教授详情时包含 `paper_summaries`
- **AND** 每条总结包含标题、摘要与关键词

#### Scenario: Manual-only update
- **WHEN** 用户仅提交 `manual_patch` 且无来源输入
- **THEN** 系统仍可完成教授信息更新

#### Scenario: Keep existing update endpoint compatible
- **WHEN** 现有客户端继续调用 PUT `/api/professors/{id}`
- **THEN** 维持向后兼容的基础字段更新行为
- **AND** 不强制要求走预览流程

### Requirement: Profile Chat API

The system SHALL provide REST API endpoints for AI interviewer chat and profile refinement.

#### Scenario: Send chat message
- **WHEN** `POST /api/profiles/{id}/chat` with `{ "message": "...", "history": [...] }`
- **AND** the profile belongs to the current user
- **THEN** the backend constructs an interviewer prompt using the profile's `profile_analysis`, `academic_profile`, chat history, and the new message
- **AND** returns `{ "reply": "AI interviewer response" }`

#### Scenario: Chat with empty history
- **WHEN** `POST /api/profiles/{id}/chat` with `{ "message": "开始", "history": [] }`
- **THEN** the AI interviewer reviews the profile and sends an opening question about the most significant gap

#### Scenario: Refine profile from chat
- **WHEN** `POST /api/profiles/{id}/chat/refine` with `{ "history": [...] }`
- **AND** the profile belongs to the current user
- **THEN** the backend enriches the manual inputs with chat-derived information
- **AND** re-runs the two-stage profile generation pipeline (analyze + build)
- **AND** saves the updated `academic_profile`, `profile_analysis`, `evidence_notes`, `conflict_notes`
- **AND** returns the updated profile

#### Scenario: Chat on non-existent profile
- **WHEN** `POST /api/profiles/{id}/chat` for a profile that does not exist or does not belong to the user
- **THEN** returns 404 error

#### Scenario: LLM unavailable
- **WHEN** the LLM API key is not configured or the API is unreachable
- **THEN** returns 503 error with a descriptive message

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

### Requirement: Dashboard API

系统 SHALL 提供 Dashboard 数据聚合 API。

#### Scenario: Get dashboard statistics
- **WHEN** GET `/api/dashboard/stats`
- **AND** 用户已认证
- **THEN** 返回当前用户的统计数据：
  - `profile_count`: 简历数量
  - `professor_count`: 教授数量
  - `match_count`: 匹配结果数量
  - `letter_count`: 已生成邮件数量

#### Scenario: Get recent activity
- **WHEN** GET `/api/dashboard/recent`
- **AND** 用户已认证
- **THEN** 返回最近活动数据：
  - `recent_profiles`: 最近更新的 5 条简历（id, title, updated_at）
  - `recent_professors`: 最近添加的 5 条教授（id, name, affiliation, created_at）

