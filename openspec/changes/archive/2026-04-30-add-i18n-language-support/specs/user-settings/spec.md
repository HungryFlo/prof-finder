## MODIFIED Requirements
### Requirement: UserSettings Model

系统 SHALL 定义 UserSettings 模型存储用户个性化配置。

#### Scenario: Settings fields
- **WHEN** 创建用户设置记录
- **THEN** 包含以下字段：
  - `id`: 主键
  - `user_id`: 所属用户ID（外键，唯一）
  - `deepseek_api_key`: DeepSeek API Key（加密存储）
  - `deepseek_base_url`: API Base URL（默认为 https://api.deepseek.com/v1）
  - `request_delay`: 爬虫请求延时（默认 3 秒）
  - `profile_language`: LLM 生成内容的默认语言（默认 "zh"，可选 "zh"/"en"）
  - `created_at`: 创建时间
  - `updated_at`: 更新时间

#### Scenario: Default settings
- **WHEN** 用户注册
- **THEN** 自动创建默认设置记录
- **AND** 使用环境变量中的默认值（如有）
- **AND** `profile_language` 默认为 "zh"

#### Scenario: Update settings
- **WHEN** 用户更新设置
- **THEN** 更新对应字段
- **AND** 刷新 `updated_at` 时间戳

#### Scenario: Language preference
- **WHEN** 用户设置 `profile_language` 为 "en"
- **THEN** 后续 LLM 生成内容（学生画像、教授科研画像、论文总结）默认使用英文
- **AND** 用户可在各页面手动切换本次生成的语言
