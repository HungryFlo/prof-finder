## MODIFIED Requirements

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

#### Scenario: Store manually added professor
- **WHEN** 用户手动添加教授
- **THEN** 至少需要 `name` 字段，其他字段可选
- **AND** 教授关联到当前用户

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

#### Scenario: LLM-generated paper summary
- **WHEN** 来源输入可提供论文文本内容
- **THEN** 系统优先使用 LLM 生成 `summary` 与 `keywords`
- **AND** 若 LLM 不可用则降级到规则摘要，保证流程可用

#### Scenario: Refresh professor data
- **WHEN** 用户请求更新教授信息
- **AND** 教授有 Google Scholar 链接
- **THEN** 重新爬取数据并更新记录
- **AND** 刷新 `updated_at` 时间戳

#### Scenario: User-isolated professor pool
- **WHEN** 用户 A 添加教授
- **THEN** 用户 B 无法看到该教授
- **AND** 每个用户维护独立的教授池

## ADDED Requirements

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
