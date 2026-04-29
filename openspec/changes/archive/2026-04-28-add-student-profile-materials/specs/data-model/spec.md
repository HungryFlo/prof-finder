## MODIFIED Requirements
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
