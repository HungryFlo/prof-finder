## 1. OpenSpec

- [x] 1.1 编写 `proposal.md` 与 spec delta
- [x] 1.2 运行 `openspec validate update-ai-chat-to-dialog --strict --no-interactive`

## 2. 前端实现

- [x] 2.1 重构 `ProfileChatPanel.vue`：移除外层 `v-if="visible"` 包裹的 inline div，改为接受 `v-model:show` 的弹窗模式（使用 Naive UI `NDrawer`）
- [x] 2.2 更新 `ProfileDetailView.vue`：移除内联嵌入与 toggle 逻辑，改为点击 "AI 优化" 按钮打开弹窗
- [x] 2.3 保留弹窗内的聊天状态（关闭后不销毁组件实例），确保重新打开时对话历史仍在

## 3. 验证

- [ ] 3.1 手动验证：打开弹窗、发送消息、关闭弹窗、重新打开、确认历史保留
- [ ] 3.2 手动验证：弹窗内点击"优化画像"成功后，ProfileDetailView 数据正确刷新
