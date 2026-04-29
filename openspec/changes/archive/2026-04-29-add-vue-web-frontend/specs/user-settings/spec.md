# 用户设置规格

## ADDED Requirements

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
  - `created_at`: 创建时间
  - `updated_at`: 更新时间

#### Scenario: Default settings
- **WHEN** 用户注册
- **THEN** 自动创建默认设置记录
- **AND** 使用环境变量中的默认值（如有）

#### Scenario: Update settings
- **WHEN** 用户更新设置
- **THEN** 更新对应字段
- **AND** 刷新 `updated_at` 时间戳

---

### Requirement: API Key Security

系统 SHALL 安全处理用户的 API Key。

#### Scenario: Store API key
- **WHEN** 用户保存 API Key
- **THEN** 以加密形式存储在数据库

#### Scenario: Display API key
- **WHEN** 返回 API Key 给前端
- **THEN** 仅显示脱敏形式（如 `sk-xxxx...xxxx`）

#### Scenario: Use API key
- **WHEN** 系统需要调用 DeepSeek API
- **THEN** 优先使用用户配置的 Key
- **IF** 用户未配置
- **THEN** 使用环境变量中的默认 Key（如有）
- **OTHERWISE** 返回错误提示

---

### Requirement: Settings Isolation

系统 SHALL 确保用户设置数据隔离。

#### Scenario: User A settings
- **WHEN** 用户 A 更新设置
- **THEN** 不影响用户 B 的设置

#### Scenario: Settings per user
- **WHEN** 用户请求设置
- **THEN** 仅返回当前用户的设置
