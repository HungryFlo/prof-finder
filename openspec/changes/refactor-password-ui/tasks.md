## 1. OpenSpec
- [x] 1.1 Create proposal.md / spec deltas
- [ ] 1.2 Run `openspec validate refactor-password-ui --strict --no-interactive`

## 2. Frontend - 提取共享组件
- [x] 2.1 创建 `PasswordRequirementCheck` 组件，包含密码要求列表（最小长度、最大长度）及实时勾叉状态
- [x] 2.2 提取或复用 `usePasswordChecks` composable
- [x] 2.3 组件支持 `v-model` 绑定密码值，内部计算校验状态

## 3. Frontend - 替换现有实现
- [x] 3.1 RegisterView 替换为使用 `PasswordRequirementCheck` 组件
- [x] 3.2 ChangePasswordView 替换为使用 `PasswordRequirementCheck` 组件
- [x] 3.3 SettingsView 密码修改区域替换为使用 `PasswordRequirementCheck` 组件
- [x] 3.4 删除 RegisterView 和 ChangePasswordView 中重复的密码校验 CSS 和逻辑

## 4. Frontend - Bug 修复
- [x] 4.1 修复 SettingsView 中 `handleChangePassword` 使用的错误 i18n key（`auth.passwordMismatch` → `auth.passwordMinLength`）

## 5. i18n
- [x] 5.1 确保密码相关的 i18n keys 在三个页面中一致使用

## 6. Validation
- [ ] 6.1 手动验证：注册页面密码校验正常
- [ ] 6.2 手动验证：强制修改密码页面校验正常
- [ ] 6.3 手动验证：设置页面修改密码校验正常且有实时提示
- [ ] 6.4 Run `openspec validate refactor-password-ui --strict --no-interactive`
