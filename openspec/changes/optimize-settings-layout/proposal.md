# Change: 优化设置页面空间布局

## Why
当前 Settings 页面三个卡片垂直堆叠，`label-placement="left"` 在宽屏上右侧有大量空白，空间利用率低。API 配置和自动化设置可以并排放置，减少页面滚动。

## What Changes
- 使用 `NGrid`（x-gap / y-gap）将 API 配置和 Professor Auto-Enrich 两个卡片并排显示（左侧 API 配置，右侧自动化设置）
- 修改密码卡片保持全宽，放在下方
- 调整表单 label-width 以适应并排布局
- 确保在窄屏（< 900px）时自动回退为单列堆叠

## Impact
- Affected specs: `web-frontend`
- Affected code: `frontend/src/views/settings/SettingsView.vue`
