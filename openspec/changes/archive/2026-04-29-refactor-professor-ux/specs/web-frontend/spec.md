## MODIFIED Requirements

### Requirement: Professor Management Page

系统 SHALL 提供教授管理页面。

#### Scenario: Professor list
- **WHEN** 用户访问 `/professor`
- **THEN** 显示教授列表表格
- **AND** 表格列：姓名（可点击链接）、机构、研究方向（标签）、H-Index、操作
- **AND** 支持分页
- **AND** 支持批量选择、批量删除、批量更新、批量生成画像

#### Scenario: Click professor name
- **WHEN** 用户点击教授的姓名
- **THEN** 打开右侧 ProfessorSummaryDrawer
- **AND** 显示教授基本信息和科研画像（若已生成）
- **AND** 不显示论文列表

#### Scenario: View professor summary
- **WHEN** 用户点击某教授的「查看」
- **THEN** 打开右侧 ProfessorSummaryDrawer（同点击姓名行为）
- **AND** 显示基本信息和科研画像

#### Scenario: Edit professor
- **WHEN** 用户点击某教授的「编辑」
- **THEN** 跳转到 `/professor/{id}`（统一的详情/编辑页面）

#### Scenario: Add by Scholar link
- **WHEN** 用户点击「Scholar 链接添加」
- **THEN** 打开 Modal 输入 Google Scholar URL
- **AND** 提交后创建异步任务爬取信息并添加
- **AND** 任务完成后刷新列表

#### Scenario: Add manually
- **WHEN** 用户点击「手动添加」
- **THEN** 打开表单 Modal
- **AND** 填写姓名、机构、研究方向等后提交

#### Scenario: Refresh professor
- **WHEN** 用户点击「更新」
- **THEN** 同步重新爬取 Google Scholar 数据

#### Scenario: Generate profile from list
- **WHEN** 用户点击「画像」
- **THEN** 为该教授创建异步科研画像生成任务
- **AND** 任务完成后刷新列表

#### Scenario: University crawl
- **WHEN** 用户点击「院校官网批量添加」
- **THEN** 打开 Modal 选择目标院校
- **AND** 提交后创建异步爬取任务

---

## ADDED Requirements

### Requirement: Professor Summary Drawer

系统 SHALL 提供可复用的教授摘要抽屉组件，用于快速查看教授基本信息和科研画像。

#### Scenario: Open summary drawer
- **WHEN** `ProfessorSummaryDrawer` 的 `show` prop 变为 true
- **AND** `professorId` prop 有效
- **THEN** 调用 `GET /api/professors/{id}` 获取教授详情
- **AND** 显示：姓名、机构、邮箱、主页、H-Index、总引用、研究方向标签

#### Scenario: Display research profile
- **WHEN** 教授详情中存在 `research_profile`
- **THEN** 显示科研画像 Markdown 内容
- **AND** 显示生成时间戳

#### Scenario: Navigate to detail
- **WHEN** 用户点击「查看详情」按钮
- **THEN** 跳转到 `/professor/{id}`
- **AND** 关闭抽屉

#### Scenario: Close drawer
- **WHEN** 用户点击关闭按钮或抽屉外部区域
- **THEN** 发送 `close` 事件
- **AND** 父组件更新 `show` prop 为 false

---

### Requirement: Professor Detail Page

系统 SHALL 提供统一的教授详情/编辑页面，合并查看与编辑功能，以及统一的论文数据展示。

#### Scenario: Open detail page
- **WHEN** 用户访问 `/professor/{id}`
- **THEN** 加载该教授的完整信息
- **AND** 加载关联的 SourceInput 列表
- **AND** 显示所有卡片区域

#### Scenario: Edit basic info
- **WHEN** 用户修改基本字段（姓名、机构、邮箱、主页、研究方向、手工备注）
- **AND** 点击「保存」
- **THEN** 调用 `PUT /api/professors/{id}` 直接保存
- **AND** 显示成功提示

#### Scenario: Scholar refresh from detail page
- **WHEN** 用户在详情页点击「Scholar更新」
- **THEN** 调用 `POST /api/professors/{id}/refresh` 同步更新
- **AND** 刷新页面数据
- **AND** 若存在 paper_summaries，弹出确认提示（refresh 会清空 paper_summaries）

#### Scenario: Fetch publication abstracts
- **WHEN** 用户点击「获取论文摘要」
- **THEN** 调用 `POST /api/professors/{id}/fill-publications` 创建异步任务
- **AND** 任务完成后自动刷新页面数据
- **AND** 论文列表中显示已获取的摘要

#### Scenario: Summarize source inputs
- **WHEN** 用户点击「论文总结」
- **THEN** 过滤出尚未总结的 SourceInput
- **AND** 调用 `POST /api/professors/{id}/summarize-sources` 创建异步任务
- **AND** 任务完成后自动刷新页面数据
- **AND** 论文总结列表显示新生成的总结

#### Scenario: Unified paper display
- **WHEN** 教授详情页加载完成
- **THEN** 论文列表（Publications 卡片）以表格形式显示 Scholar 论文
- **AND** 表格列包含：标题、年份、引用数、期刊、摘要（可展开）
- **AND** 论文总结（Paper Summaries 卡片）以列表形式显示来源输入的总结
- **AND** 当论文标题与某条总结标题匹配时，论文行显示关联标识

#### Scenario: Upload source inputs on detail page
- **WHEN** 用户在详情页上传 PDF 或提交 ArXiv 链接
- **THEN** 使用 SourceInputPanel 组件处理
- **AND** 新来源添加到当前教授关联

#### Scenario: Generate research profile from detail page
- **WHEN** 用户点击「生成科研画像」
- **THEN** 调用 `POST /api/professors/{id}/generate-profile` 创建异步任务
- **AND** 任务完成后自动刷新显示新生成的画像

#### Scenario: Backward compatible route
- **WHEN** 用户访问旧路径 `/professor/{id}/edit`
- **THEN** 自动重定向到 `/professor/{id}`
