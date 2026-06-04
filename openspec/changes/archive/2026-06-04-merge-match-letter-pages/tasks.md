## 1. OpenSpec
- [x] 1.1 Create proposal.md / spec deltas
- [x] 1.2 Run `openspec validate merge-match-letter-pages --strict --no-interactive`

## 2. Frontend - Match 页面增强
- [x] 2.1 加宽 MatchResultsView 详情弹窗从 620px 到 900px
- [x] 2.2 在详情弹窗中集成邮件编辑区域（textarea，15 行，展示已生成邮件内容）
- [x] 2.3 详情弹窗中添加「复制到剪贴板」「保存邮件」按钮
- [x] 2.4 详情弹窗中未生成邮件时显示「生成邮件」按钮
- [x] 2.5 详情弹窗中已生成邮件时显示「重新生成」按钮
- [x] 2.6 Match 页面 header 中保留邮件语言选择器（zh/en）
- [x] 2.7 详情弹窗底部区域使用 NDivider 分隔匹配信息和邮件编辑区

## 3. Frontend - 清理 Letter 页面
- [x] 3.1 删除 `frontend/src/views/letter/LetterListView.vue`
- [x] 3.2 从 router/index.ts 移除 `/letter` 路由
- [x] 3.3 从 MainLayout 侧边栏菜单移除「联络邮件」入口
- [x] 3.4 清理 `frontend/src/api/letters.ts` 中不再需要的列表/分页相关 API 调用（保留生成/保存/复制相关）

## 4. i18n
- [x] 4.1 移除 letter 列表页面相关的 i18n keys
- [x] 4.2 确保邮件编辑相关的 i18n keys 在 match 页面中可正常使用
- [x] 4.3 新增 match 详情弹窗中邮件编辑区域的 i18n keys（如「复制到剪贴板」「保存邮件」「邮件内容」等）

## 5. Validation
- [x] 5.1 手动验证：Match 页面详情弹窗中邮件生成、编辑、复制、保存功能正常
- [x] 5.2 手动验证：侧边栏不再显示「联络邮件」
- [x] 5.3 手动验证：直接访问 `/letter` 路由时正确重定向
- [x] 5.4 Run `openspec validate merge-match-letter-pages --strict --no-interactive`
