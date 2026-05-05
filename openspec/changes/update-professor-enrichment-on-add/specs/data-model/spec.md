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
