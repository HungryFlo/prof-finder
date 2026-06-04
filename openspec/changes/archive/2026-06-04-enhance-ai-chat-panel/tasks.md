## 1. OpenSpec
- [x] 1.1 Create proposal.md / spec deltas
- [x] 1.2 Run `openspec validate enhance-ai-chat-panel --strict --no-interactive`

## 2. Frontend - Suggestions 组件
- [x] 2.1 在 ProfileChatPanel 空状态下方添加 `Suggestions` 组件
- [x] 2.2 配置 3-4 个预设快捷提问（随 i18n 切换）
- [x] 2.3 点击 suggestion 自动填充到输入框并发送

## 3. Frontend - ConversationScrollButton
- [x] 3.1 在 `Conversation` 内添加 `ConversationScrollButton` 组件
- [x] 3.2 验证长对话滚动时按钮正确显示/隐藏

## 4. Frontend - MessageActions
- [x] 4.1 在 AI 回复消息下方添加 `MessageToolbar` + `MessageActions` 组件
- [x] 4.2 添加「复制」`MessageAction`，点击复制 AI 回复内容到剪贴板
- [x] 4.3 添加「重新生成」`MessageAction`，点击重新发送上一条用户消息

## 5. i18n
- [x] 5.1 新增快捷提问的中英文 i18n keys
- [x] 5.2 新增消息操作按钮的 i18n keys（tooltip 文本）

## 6. Validation
- [x] 6.1 手动验证：空状态显示 suggestion pills 且可点击发送
- [x] 6.2 手动验证：长对话中回到底部按钮正常工作
- [x] 6.3 手动验证：AI 回复下方复制和重新生成按钮正常工作
- [x] 6.4 Run `openspec validate enhance-ai-chat-panel --strict --no-interactive`
