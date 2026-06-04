# Change: 提取共享密码校验组件

## Why
RegisterView 和 ChangePasswordView 中有几乎完全相同的密码校验 UI（实时密码要求检查、勾叉指示器、CSS 样式），代码重复。SettingsView 中的密码修改表单缺少实时密码强度提示，体验与其他两个页面不一致。此外 SettingsView 中有一个 i18n key 错误（用 `auth.passwordMismatch` 作为最小长度错误信息）。

## What Changes
- 提取共享的 `PasswordRequirementCheck` 组件，包含：
  - 密码要求列表（最小长度、最大长度）及实时勾叉状态
  - 相关 CSS 样式
- 创建 `usePasswordChecks` composable（如尚未独立提取）
- RegisterView、ChangePasswordView、SettingsView 统一使用新组件
- 修复 SettingsView 中密码校验的 i18n key 错误
- SettingsView 密码修改区域增加实时密码强度提示，与注册/强制修改密码页面一致

## Impact
- Affected specs: `web-frontend`
- Affected code: `frontend/src/views/auth/RegisterView.vue`, `frontend/src/views/auth/ChangePasswordView.vue`, `frontend/src/views/settings/SettingsView.vue`, 新增 `frontend/src/components/PasswordRequirementCheck.vue`（或类似命名）
