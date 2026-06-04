## 1. OpenSpec
- [x] 1.1 Create proposal.md / spec deltas
- [x] 1.2 Run `openspec validate add-dark-mode-toggle --strict --no-interactive`

## 2. Frontend - Theme Store / Composable
- [x] 2.1 创建 `useTheme` composable 或 Pinia store，管理 dark/light 状态
- [x] 2.2 实现 localStorage 持久化（key: `prof-finder-theme`）
- [x] 2.3 实现 HTML root class 切换（`.dark`）
- [x] 2.4 初始化时从 localStorage 读取偏好

## 3. Frontend - UI 集成
- [x] 3.1 在 MainLayout Header 中添加深色模式切换按钮（NButton + 太阳/月亮图标）
- [x] 3.2 App.vue 中根据 theme 状态切换 Naive UI 的 `darkTheme` 和 light theme
- [x] 3.3 确保 CSS 变量在 dark 模式下正确切换

## 4. Validation
- [x] 4.1 手动验证：点击切换按钮在 light/dark 间切换
- [x] 4.2 手动验证：刷新后主题偏好保持
- [x] 4.3 手动验证：Naive UI 组件在 dark 模式下正确渲染
- [x] 4.4 Run `openspec validate add-dark-mode-toggle --strict --no-interactive`
