# data-model Specification

## Purpose

定义 Prof-Finder 的持久化数据模型（用户、学生画像、教授、匹配结果、后台任务、用户设置等）及多用户数据隔离约定，作为 CLI、REST API 与后台任务实现的结构基础。
## Requirements
### Requirement: User Model

系统 SHALL 定义 User 模型支持多用户。

#### Scenario: Create user
- **WHEN** 新用户首次使用系统
- **THEN** 创建用户记录，包含：
  - `id`: 主键
  - `username`: 用户名（唯一标识）
  - `created_at`: 创建时间

#### Scenario: Switch user
- **WHEN** 用户指定不同的用户名
- **THEN** 切换到对应用户的数据上下文

---

### Requirement: UserProfile Model

系统 SHALL 定义 UserProfile 模型存储用户画像信息，支持一个用户多份画像。

#### Scenario: Store parsed resume
- **WHEN** 用户上传或输入简历
- **THEN** 系统保存以下字段：
  - `id`: 主键
  - `user_id`: 所属用户ID（外键）
  - `name`: 简历中的姓名
  - `title`: 画像标题/版本名（如"申请NLP方向"）
  - `education`: 教育背景列表（JSON格式，含学位、学校、专业、时间）
  - `research_experience`: 科研经历列表（JSON格式）
  - `projects`: 项目经历列表（JSON格式）
  - `skills`: 技能列表（字符串数组）
  - `raw_content`: 原始简历文本
  - `is_active`: 是否为当前激活的画像
  - `created_at`: 创建时间
  - `updated_at`: 更新时间

#### Scenario: Store generated student academic profile
- **WHEN** 用户通过多材料生成学生画像
- **THEN** 系统保存以下附加字段：
  - `profile_materials`: 材料元数据列表（JSON格式，含来源类型、文件名或手填字段名）
  - `manual_inputs`: 用户直接填写的研究兴趣、个人陈述、研究计划和备注（JSON格式）
  - `academic_profile`: 生成的学生学术画像内容（JSON 或 Markdown 文本）
  - `profile_analysis`: 画像 analyzer 的结构化分析结果（JSON格式）
  - `evidence_notes`: 关键画像结论的证据摘要（JSON格式）
  - `conflict_notes`: 手填内容与文件材料冲突的说明（JSON格式）
  - `profile_generated_at`: 画像生成时间

#### Scenario: Update profile
- **WHEN** 用户编辑画像
- **THEN** 更新对应字段并刷新 `updated_at` 时间戳

#### Scenario: Multiple profiles per user
- **WHEN** 用户创建新画像
- **AND** 已存在其他画像
- **THEN** 新画像设为 `is_active=True`
- **AND** 其他画像设为 `is_active=False`

#### Scenario: Switch active profile
- **WHEN** 用户选择切换到另一份画像
- **THEN** 更新 `is_active` 状态

#### Scenario: Existing resume-only profiles remain valid
- **WHEN** 数据库中存在缺少学生学术画像字段的旧画像
- **THEN** 系统仍可读取、展示、匹配和编辑该画像

### Requirement: Professor Model

系统 SHALL 定义 Professor 模型存储教授信息，每个用户有独立的教授池，并支持新增后的持续手动修订与来源追踪。

#### Scenario: Store professor from Scholar
- **WHEN** 从 Google Scholar 爬取教授信息
- **THEN** 系统保存以下字段：
  - `id`: 主键
  - `user_id`: 所属用户ID（外键，用户独立的教授池）
  - `name`: 姓名
  - `affiliation`: 所属院系/大学
  - `research_interests`: 研究方向列表（JSON格式）
  - `homepage`: 个人主页URL（可选）
  - `google_scholar_id`: Google Scholar ID
  - `google_scholar_url`: Google Scholar 页面链接
  - `publications`: 代表论文列表（JSON格式，含标题、年份、引用数）
  - `h_index`: H-Index（可选）
  - `citations`: 总引用数（可选）
  - `email`: 邮箱（可选）
  - `manual_notes`: 用户手工备注（可选）
  - `created_at`: 创建时间
  - `updated_at`: 更新时间
- **AND** 在爬取入库完成后，系统 SHALL 尽快自动填充英文 `paper_summaries`（可标记 `source_type` 为 `scholar_pub` 等）并生成 `research_profile` 相关字段（在 API/CLI 语义下为异步或同步 pipeline，见 rest-api / cli）

#### Scenario: Store manually added professor
- **WHEN** 用户手动添加教授
- **THEN** 至少需要 `name` 字段，其他字段可选
- **AND** 教授关联到当前用户
- **AND** 创建完成后系统 SHALL 触发科研画像生成 pipeline（在数据稀疏时按 professor-profile 规范输出不足证据标记）

#### Scenario: Update professor data by manual edit
- **WHEN** 用户在教授编辑流程中手动修改字段
- **THEN** 更新教授记录
- **AND** 刷新 `updated_at` 时间戳

#### Scenario: Update professor data by external sources
- **WHEN** 用户上传论文 PDF 或提交 ArXiv 链接并确认应用
- **THEN** 系统将来源提取结果写入教授字段（如研究方向、论文列表、备注）
- **AND** 记录来源追踪关系用于审计与回溯

#### Scenario: Persist paper summaries from source inputs
- **WHEN** 用户确认应用 PDF 或 ArXiv 来源输入
- **THEN** 系统为教授写入结构化 `paper_summaries` 字段
- **AND** 每条总结包含 `title`、`summary`、`keywords` 与来源关联信息
- **AND** 后续匹配流程可读取这些总结内容

#### Scenario: Persist paper summaries from Scholar publications
- **WHEN** 系统自动 enrichment pipeline 处理带有 Google Scholar 出版物列表的教授
- **THEN** 系统 SHALL 将前 N 篇（配置上限）出版物的英文摘要写入 `paper_summaries`
- **AND** 每条记录 SHALL 可区分来源（例如 `source_type: scholar_pub` 与可选 `scholar_author_pub_id`）
- **AND** 该行为与 PDF/ArXiv 来源的摘要条目在结构上兼容，供匹配与画像共用

#### Scenario: LLM-generated paper summary
- **WHEN** 来源输入可提供论文文本内容
- **THEN** 系统优先使用 LLM 生成 `summary` 与 `keywords`
- **AND** 若 LLM 不可用则降级到规则摘要，保证流程可用

#### Scenario: Refresh professor data
- **WHEN** 用户请求更新教授信息
- **AND** 教授有 Google Scholar 链接
- **THEN** 重新爬取数据并更新记录
- **AND** 刷新 `updated_at` 时间戳
- **AND** 系统 SHALL 移除现有 `paper_summaries` 中来自 Scholar 自动摘要的条目（例如 `source_type` 为 `scholar_pub`），SHALL NOT 删除来自 PDF/ArXiv 来源输入的条目
- **AND** 更新完成后 SHALL 再次运行自动 enrichment 以重建 Scholar 衍生摘要与科研画像

#### Scenario: User-isolated professor pool
- **WHEN** 用户 A 添加教授
- **THEN** 用户 B 无法看到该教授
- **AND** 每个用户维护独立的教授池

### Requirement: MatchRecord Model

系统 SHALL 定义 MatchRecord 模型存储匹配结果。

#### Scenario: Store match result
- **WHEN** 执行匹配算法
- **THEN** 为每个教授创建匹配记录：
  - `id`: 主键
  - `user_profile_id`: 关联的用户简历ID
  - `professor_id`: 关联的教授ID
  - `score`: 匹配分数（0-100）
  - `match_reasons`: 匹配原因列表（JSON格式）
  - `created_at`: 创建时间

#### Scenario: Store generated letter
- **WHEN** 为某教授生成联络邮件
- **THEN** 更新匹配记录：
  - `letter_generated`: 标记为 True
  - `letter_content`: 存储邮件内容
  - `letter_generated_at`: 生成时间

---

### Requirement: Database Initialization

系统 SHALL 支持自动初始化数据库。

#### Scenario: First run
- **WHEN** 首次运行任何命令
- **AND** 数据库文件不存在
- **THEN** 自动创建 SQLite 数据库
- **AND** 创建所有必要的表结构

#### Scenario: Database path configuration
- **WHEN** 环境变量 `DATABASE_PATH` 已配置
- **THEN** 使用配置的路径创建/连接数据库
- **OTHERWISE** 使用默认路径 `./data/prof_finder.db`

### Requirement: SourceInput Model

系统 SHALL 定义可复用的 SourceInput 模型，用于承载 PDF 与 ArXiv 链接输入，并支持在不同编辑页面复用。

#### Scenario: Create PDF source input
- **WHEN** 用户上传 PDF 文件
- **THEN** 创建 `SourceInput` 记录，包含：
  - `id`: 主键
  - `user_id`: 所属用户ID
  - `source_type`: `pdf`
  - `original_name`: 原始文件名
  - `storage_path`: 文件存储路径（可选）
  - `extracted_text`: 提取文本（可选）
  - `extracted_markdown`: 使用 `pymupdf4llm` 提取的 Markdown（可选）
  - `status`: 处理状态（`pending/succeeded/failed`）
  - `error_message`: 失败原因（可选）
  - `created_at`: 创建时间
  - `updated_at`: 更新时间

#### Scenario: Create ArXiv source input
- **WHEN** 用户提交 ArXiv 链接
- **THEN** 创建 `SourceInput` 记录，包含：
  - `source_type`: `arxiv`
  - `source_url`: 用户提交链接
  - `canonical_id`: 规范化 ArXiv ID
  - `title`: 论文标题（可选）
  - `abstract`: 摘要（可选）
  - `pdf_url`: 来自 ArXiv 官方 API 的 PDF 链接（可选）
  - `downloaded_pdf_path`: 下载后的临时 PDF 路径（可选）
  - `extracted_markdown`: 通过 `pymupdf4llm` 解析得到的 Markdown（可选）
  - `metadata_only`: 是否仅保存元数据（默认 `false`）
  - `status`: 处理状态（`pending/succeeded/failed`）

#### Scenario: ArXiv source reuses PDF parsing pipeline
- **WHEN** ArXiv 链接处理成功获取 PDF
- **THEN** 系统 MUST 下载 PDF 并走与手动上传 PDF 相同的解析流程
- **AND** 保证两类来源在下游更新中的文本结构一致

#### Scenario: Remove temporary PDF after parse
- **WHEN** ArXiv PDF 解析完成（成功或失败）
- **THEN** 系统 SHOULD 删除临时下载文件释放空间
- **AND** 若删除失败，应记录日志并由兜底清理机制处理

#### Scenario: Save metadata when ArXiv PDF download fails
- **WHEN** ArXiv 官方 API 元数据获取成功
- **AND** PDF 下载失败
- **THEN** 系统仍保存 `canonical_id/title/abstract/pdf_url` 等元数据
- **AND** 标记 `metadata_only=true`
- **AND** 保存失败原因供前端提示“稍后重试 PDF 解析”

#### Scenario: Reuse source input for multiple entity editors
- **WHEN** 未来新增个人信息修改页面
- **THEN** 该页面可直接复用 `SourceInput` 模型与处理流程
- **AND** 不需要新增一套独立的 PDF/ArXiv 输入数据结构

### Requirement: UserSettings auto-enrichment columns

`user_settings` 表 SHALL 持久化三个布尔列，用于控制写入或 Scholar 同步后的自动教授 enrichment 子步。

#### Scenario: New columns exist after migration
- **WHEN** 应用在已有数据库上启动并完成迁移
- **THEN** `user_settings` 包含 `auto_enrich_on_save_fetch_publication_details`、`auto_enrich_on_save_paper_summaries`、`auto_enrich_on_save_research_profile` 列
- **AND** 现有行的默认值为 true（与历史行为一致）

### Requirement: BackgroundTask Table

系统 SHALL 使用 `background_tasks` 表持久化后台任务状态。

#### Scenario: BackgroundTask schema
- **WHEN** 数据库初始化
- **THEN** 创建 `background_tasks` 表，包含以下列：
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `task_id` VARCHAR(36) UNIQUE NOT NULL（UUID）
  - `task_type` VARCHAR(50) NOT NULL
  - `task_name` VARCHAR(200) NOT NULL
  - `user_id` INTEGER NOT NULL REFERENCES users(id)
  - `status` VARCHAR(20) NOT NULL DEFAULT 'pending'
  - `total` INTEGER NOT NULL DEFAULT 0
  - `current` INTEGER NOT NULL DEFAULT 0
  - `success_count` INTEGER NOT NULL DEFAULT 0
  - `failed_count` INTEGER NOT NULL DEFAULT 0
  - `message` TEXT DEFAULT ''
  - `error_message` TEXT DEFAULT ''
  - `results` JSON DEFAULT '[]'
  - `cancel_requested` BOOLEAN DEFAULT FALSE
  - `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
  - `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP

#### Scenario: Task ID uniqueness
- **WHEN** 创建新任务
- **THEN** `task_id` 使用 UUID4 生成，确保全局唯一

#### Scenario: Cascade on user delete
- **WHEN** 用户被删除
- **THEN** 关联的 `background_tasks` 行由外键约束处理（或手动清理）

