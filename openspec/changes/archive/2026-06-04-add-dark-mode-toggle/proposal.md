# Change: 添加深色模式切换

## Why
CSS 中已有完整的 `.dark` 主题定义（style.css 中包含 dark 变量），但 UI 上没有切换按钮，用户无法使用深色模式。只需在 Header 加一个 toggle 即可启用已有的深色主题。

## What Changes
- 在 MainLayout 的 Header 中添加深色模式切换按钮（太阳/月亮图标）
- 点击切换 Naive UI 的 `darkTheme` 和自定义 light theme
- 同步切换 HTML root class（`.dark`）以激活 CSS 变量
- 深色模式偏好保存到 localStorage，刷新后保持
- 确保 Naive UI 组件在深色模式下正确渲染（NConfigProvider theme 切换）

## Impact
- Affected specs: `web-frontend`
- Affected code: `frontend/src/layouts/MainLayout.vue`, `frontend/src/App.vue`（theme 切换逻辑）, `frontend/src/stores/` 或 `frontend/src/composables/`（新增 theme store 或 composable）
