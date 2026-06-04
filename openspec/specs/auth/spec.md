# auth Specification

## Purpose

定义 Web 多用户认证：注册与登录、JWT 访问/刷新令牌、首次登录与管理员重置后的强制改密，以及管理员对用户密码的重置能力。面向本地部署场景，凭据保存在用户自选的 SQLite 数据库中。
## Requirements
### Requirement: User Registration

系统 SHALL 支持用户注册，仅需用户名和密码。

#### Scenario: Successful registration
- **WHEN** 用户提交有效的用户名和密码
- **AND** 用户名未被占用
- **THEN** 创建新用户账户
- **AND** 密码以带随机盐的 SHA-256 单向哈希存储（`salt$hash` 格式）
- **AND** 返回成功响应

#### Scenario: Username already exists
- **WHEN** 用户提交的用户名已被占用
- **THEN** 返回错误：用户名已存在

#### Scenario: Invalid password
- **WHEN** 密码长度少于 6 个字符
- **THEN** 返回错误：密码至少需要 6 个字符

#### Scenario: Cannot register as root
- **WHEN** 用户尝试注册用户名为 `root`
- **THEN** 返回错误：该用户名为系统保留

---

### Requirement: Admin Account Initialization

系统 SHALL 在启动时自动创建管理员账户。

#### Scenario: Create default admin
- **WHEN** 系统首次启动
- **AND** 数据库中不存在 `root` 用户
- **THEN** 自动创建管理员账户：
  - 用户名：`root`（或环境变量 `ADMIN_USERNAME`）
  - 密码：`root123`（或环境变量 `ADMIN_PASSWORD`）
  - `is_admin=True`
  - `must_change_password=True`（如果使用默认密码）

#### Scenario: Custom admin credentials
- **WHEN** 环境变量 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 已配置
- **THEN** 使用配置的值创建管理员账户
- **AND** `must_change_password=False`

#### Scenario: Admin already exists
- **WHEN** 系统启动
- **AND** 数据库中已存在管理员账户
- **THEN** 不做任何修改

---

### Requirement: Force Password Change

系统 SHALL 强制使用默认密码的管理员修改密码。

#### Scenario: Login with default password
- **WHEN** 管理员使用默认密码登录
- **AND** `must_change_password=True`
- **THEN** 返回特殊响应码，要求修改密码
- **AND** 前端跳转到强制修改密码页面

#### Scenario: After password change
- **WHEN** 管理员修改密码成功
- **THEN** 设置 `must_change_password=False`

---

### Requirement: User Login

系统 SHALL 支持用户登录并返回 JWT Token。

#### Scenario: Successful login
- **WHEN** 用户提交正确的用户名和密码
- **THEN** 返回 Access Token（30分钟有效）
- **AND** 返回 Refresh Token（7天有效）

#### Scenario: Invalid credentials
- **WHEN** 用户名不存在或密码错误
- **THEN** 返回错误：用户名或密码错误

---

### Requirement: Token Refresh

系统 SHALL 支持使用 Refresh Token 获取新的 Access Token。

#### Scenario: Valid refresh token
- **WHEN** 客户端提交有效的 Refresh Token
- **THEN** 返回新的 Access Token

#### Scenario: Expired refresh token
- **WHEN** Refresh Token 已过期
- **THEN** 返回 401 错误
- **AND** 客户端需重新登录

---

### Requirement: Get Current User

系统 SHALL 提供获取当前登录用户信息的接口。

#### Scenario: Valid token
- **WHEN** 请求携带有效的 Access Token
- **THEN** 返回当前用户信息（id、username、is_admin、created_at）

#### Scenario: Invalid token
- **WHEN** Token 无效或已过期
- **THEN** 返回 401 错误

---

### Requirement: Admin Password Reset

系统 SHALL 允许管理员重置任意用户的密码。

#### Scenario: Admin resets password
- **WHEN** 管理员调用重置密码接口
- **AND** 提供目标用户 ID 和新密码
- **THEN** 更新目标用户的密码哈希
- **AND** 返回成功响应

#### Scenario: Non-admin attempt
- **WHEN** 非管理员用户调用重置密码接口
- **THEN** 返回 403 错误：权限不足

#### Scenario: Admin list users
- **WHEN** 管理员调用用户列表接口
- **THEN** 返回所有用户列表（不含密码哈希）

---

### Requirement: Password Change

系统 SHALL 允许用户修改自己的密码。

#### Scenario: Successful password change
- **WHEN** 用户提交当前密码和新密码
- **AND** 当前密码验证正确
- **THEN** 更新密码哈希
- **AND** 返回成功响应

#### Scenario: Wrong current password
- **WHEN** 当前密码验证失败
- **THEN** 返回错误：当前密码错误

---

### Requirement: JWT Authentication Middleware

系统 SHALL 实现 JWT 认证中间件保护 API 端点。

#### Scenario: Protected endpoint access
- **WHEN** 请求访问受保护的 API
- **AND** 携带有效的 Access Token
- **THEN** 允许访问并注入当前用户上下文

#### Scenario: Missing token
- **WHEN** 请求未携带 Authorization header
- **THEN** 返回 401 错误

#### Scenario: Invalid token format
- **WHEN** Authorization header 格式不正确（非 Bearer token）
- **THEN** 返回 401 错误

