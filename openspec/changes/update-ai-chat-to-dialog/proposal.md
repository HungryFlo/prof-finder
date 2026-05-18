# Change: AI 画像优化聊天改为弹窗模式

## Why

当前 AI 画像优化聊天面板以内联方式嵌入 ProfileDetailView 页面流中，展开时会将下方的编辑表单推到页面底部，打断用户的编辑上下文。改为弹窗（Dialog）模式后，聊天与编辑互不干扰，用户可以随时打开/关闭弹窗而不丢失页面位置。

## What Changes

- `ProfileChatPanel` 从内联面板改为 Naive UI `NDialog` 或 `NDrawer` 弹窗组件，宽度适配聊天内容（约 480px），居中或右侧抽屉展示。
- `ProfileDetailView` 中移除内联嵌入方式，改为通过 `v-model:show` 控制弹窗显隐。
- 弹窗打开时自动触发 AI 开场白（保留现有行为）。
- 弹窗关闭时保留聊天历史（组件状态不销毁），重新打开时继续对话。
- "优化画像"按钮功能不变，成功后通过事件通知 ProfileDetailView 刷新数据。
- 移除原来的展开/收起 toggle 逻辑，改为单一 "AI 优化" 按钮打开弹窗。

## Impact

- Affected specs: `web-frontend`
- Affected code: `ProfileChatPanel.vue`, `ProfileDetailView.vue`
