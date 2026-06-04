## MODIFIED Requirements

### Requirement: Authentication Pages

系统 SHALL 提供登录和注册页面，使用共享的密码校验组件。

#### Scenario: Login page
- **WHEN** 用户访问 `/login`
- **THEN** 显示登录表单（用户名、密码）
- **AND** 登录成功后跳转到首页

#### Scenario: Register page
- **WHEN** 用户访问 `/register`
- **THEN** 显示注册表单（用户名、密码、确认密码）
- **AND** 使用共享的 `PasswordRequirementCheck` 组件显示实时密码校验
- **AND** 注册成功后跳转到登录页

#### Scenario: Force change password page
- **WHEN** 用户访问 `/change-password`
- **THEN** 显示密码修改表单（当前密码、新密码、确认密码）
- **AND** 使用共享的 `PasswordRequirementCheck` 组件显示实时密码校验
- **AND** 修改成功后跳转到首页

#### Scenario: Route guard
- **WHEN** 未登录用户访问受保护页面
- **THEN** 自动跳转到登录页
- **AND** 登录后跳回原目标页面

---

### Requirement: Settings Page

系统 SHALL 提供设置页面，包含 API 配置、自动化设置和密码修改，密码修改使用共享的密码校验组件。

#### Scenario: Settings sections
- **WHEN** 用户访问 `/settings`
- **THEN** 显示设置页面，包含：
  - 账户设置：修改密码（使用 `PasswordRequirementCheck` 组件）
  - API 配置：DeepSeek API Key、Base URL
  - 爬虫设置：请求延时

#### Scenario: Change password
- **WHEN** 用户填写「当前密码」和「新密码」并提交
- **THEN** 使用共享的 `PasswordRequirementCheck` 组件显示实时密码校验
- **AND** 修改密码
- **AND** 显示成功提示

#### Scenario: Update API key
- **WHEN** 用户填写 API Key 并保存
- **THEN** 保存到用户设置
- **AND** 显示脱敏后的 Key
