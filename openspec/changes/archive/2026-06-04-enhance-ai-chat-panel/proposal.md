# Change: 增强 AI 聊天面板功能

## Why
ProfileChatPanel 当前仅使用了 ai-elements 组件库中约 12 个组件，而库中有多个高价值组件未被使用。增加 Suggestions（快捷提示）、ConversationScrollButton（回到底部按钮）和 MessageActions（消息操作按钮：复制、重新生成）可以显著提升聊天体验，且这些组件已存在于代码库中，无需额外依赖。

## What Changes
- 在聊天空状态下方增加 `Suggestions` 组件，显示预设的快捷提问（如「介绍一下你的研究经历」「你的核心技能是什么」「你的学术目标是什么」）
- 在对话区域增加 `ConversationScrollButton`，长对话滚动时可快速回到底部
- 在 AI 回复消息下方增加 `MessageActions` + `MessageAction` 组件，支持：
  - 「复制」按钮：将 AI 回复内容复制到剪贴板
  - 「重新生成」按钮：重新发送上一条用户消息获取新回复
- 快捷提问内容随 i18n 语言切换

## Impact
- Affected specs: `web-frontend`
- Affected code: `frontend/src/components/ProfileChatPanel.vue`, `frontend/src/locales/zh.json`, `frontend/src/locales/en.json`
