## ADDED Requirements

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
