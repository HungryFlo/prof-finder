# Change: 合并匹配结果与联络邮件页面

## Why
匹配结果页和联络邮件页功能高度重叠——Match 表中每行已有 "生成邮件" 按钮和 letter status 列，Letter 页面本质上只是 Match 结果的一个子集视图。用户需要在两个页面间跳转，workflow 不连贯。合并后用户可在同一页面完成匹配查看、邮件生成与编辑的完整流程。

## What Changes
- 删除 `/letter` 路由和 `LetterListView.vue` 页面
- 从侧边栏导航菜单中移除「联络邮件」入口
- 加宽 Match 结果详情弹窗（620px → 900px），集成邮件编辑功能
  - 详情弹窗中新增邮件内容区域：展示已生成的邮件内容（可编辑 textarea）
  - 支持「复制到剪贴板」和「保存邮件」操作
  - 未生成邮件时显示「生成邮件」按钮
  - 已生成邮件时显示「重新生成」按钮
- 保留邮件语言选择器（zh/en）在 Match 页面 header 中
- i18n 移除 letter 相关的独立页面 key，保留邮件编辑相关的 key

## Impact
- Affected specs: `web-frontend`, `rest-api`
- Affected code: `frontend/src/views/match/MatchResultsView.vue`, `frontend/src/views/letter/LetterListView.vue`（删除）, `frontend/src/router/index.ts`, `frontend/src/layouts/MainLayout.vue`, `frontend/src/locales/zh.json`, `frontend/src/locales/en.json`
