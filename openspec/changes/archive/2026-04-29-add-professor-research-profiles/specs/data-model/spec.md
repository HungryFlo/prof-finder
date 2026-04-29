## MODIFIED Requirements
### Requirement: Professor Model

系统 SHALL 定义 Professor 模型存储教授信息，每个用户有独立的教授池。

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
  - `paper_summaries`: 论文摘要列表（JSON格式，含标题、摘要、关键词和来源）
  - `h_index`: H-Index（可选）
  - `citations`: 总引用数（可选）
  - `email`: 邮箱（可选）
  - `manual_notes`: 用户手动备注（可选）
  - `embedding`: 教授匹配文本的缓存向量（JSON格式，可选）
  - `created_at`: 创建时间
  - `updated_at`: 更新时间

#### Scenario: Store generated professor research profile
- **WHEN** 用户为教授生成科研画像
- **THEN** 系统保存以下附加字段：
  - `research_profile`: 生成的教师科研画像内容（JSON 或 Markdown 文本）
  - `research_profile_analysis`: 画像 analyzer 的结构化分析结果（JSON格式）
  - `research_profile_sources`: 参与画像生成的来源元数据（JSON格式）
  - `research_profile_evidence`: 关键画像结论的证据摘要（JSON格式）
  - `research_profile_conflicts`: 手动备注与材料推断冲突的说明（JSON格式）
  - `research_profile_generated_at`: 科研画像生成时间

#### Scenario: Store manually added professor
- **WHEN** 用户手动添加教授
- **THEN** 至少需要 `name` 字段，其他字段可选
- **AND** 教授关联到当前用户

#### Scenario: Update professor data
- **WHEN** 用户请求更新教授信息
- **AND** 教授有 Google Scholar 链接
- **THEN** 重新爬取数据并更新记录
- **AND** 刷新 `updated_at` 时间戳

#### Scenario: User-isolated professor pool
- **WHEN** 用户 A 添加教授
- **THEN** 用户 B 无法看到该教授
- **AND** 每个用户维护独立的教授池

#### Scenario: Existing professors remain valid
- **WHEN** 数据库中存在缺少科研画像字段的旧教授记录
- **THEN** 系统仍可读取、展示、匹配和编辑该教授
