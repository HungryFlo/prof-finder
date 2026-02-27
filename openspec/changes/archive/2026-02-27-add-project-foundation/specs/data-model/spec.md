# Data Model Specification

## ADDED Requirements

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

系统 SHALL 定义 UserProfile 模型存储用户简历信息，支持一个用户多份简历。

#### Scenario: Store parsed resume
- **WHEN** 用户上传或输入简历
- **THEN** 系统保存以下字段：
  - `id`: 主键
  - `user_id`: 所属用户ID（外键）
  - `name`: 简历中的姓名
  - `title`: 简历标题/版本名（如"申请NLP方向"）
  - `education`: 教育背景列表（JSON格式，含学位、学校、专业、时间）
  - `research_experience`: 科研经历列表（JSON格式）
  - `projects`: 项目经历列表（JSON格式）
  - `skills`: 技能列表（字符串数组）
  - `raw_content`: 原始简历文本
  - `is_active`: 是否为当前激活的简历
  - `created_at`: 创建时间
  - `updated_at`: 更新时间

#### Scenario: Update profile
- **WHEN** 用户编辑简历
- **THEN** 更新对应字段并刷新 `updated_at` 时间戳

#### Scenario: Multiple profiles per user
- **WHEN** 用户创建新简历
- **AND** 已存在其他简历
- **THEN** 新简历设为 `is_active=True`
- **AND** 其他简历设为 `is_active=False`

#### Scenario: Switch active profile
- **WHEN** 用户选择切换到另一份简历
- **THEN** 更新 `is_active` 状态

---

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
  - `h_index`: H-Index（可选）
  - `citations`: 总引用数（可选）
  - `email`: 邮箱（可选）
  - `created_at`: 创建时间
  - `updated_at`: 更新时间

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

---

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
