## MODIFIED Requirements
### Requirement: Professor Management Page

系统 SHALL 提供教授管理页面。

#### Scenario: Professor list
- **WHEN** 用户访问 `/professor`
- **THEN** 显示教授列表表格
- **AND** 表格列：姓名（可点击链接）、机构、研究方向（标签）、H-Index、操作
- **AND** 表格行内不得提供「更新」或「画像」按钮
- **AND** 支持分页
- **AND** 支持批量选择、批量删除、批量更新、批量生成画像

#### Scenario: Search professors
- **WHEN** 用户在搜索框输入关键词
- **THEN** 按姓名和机构模糊搜索教授列表
- **AND** 搜索时重置到第一页
- **AND** 支持清空搜索恢复完整列表

#### Scenario: Sort professor table
- **WHEN** 用户点击姓名、机构或 H-Index 列标题
- **THEN** 按该列升序或降序排列
- **AND** 排序时重置到第一页
- **AND** 显示排序方向指示器

#### Scenario: Filter by affiliation
- **WHEN** 用户在机构列使用筛选功能
- **THEN** 显示当前用户所有教授的去重机构列表
- **AND** 选择机构后筛选显示匹配的教授
- **AND** 筛选时重置到第一页

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

#### Scenario: Batch refresh professors from list
- **WHEN** 用户勾选至少一名教授后点击「批量更新」
- **THEN** 创建批量数据刷新异步任务，覆盖所选教授
- **AND** 任务在任务面板中可跟踪；相关链式任务（若有）完成后列表数据得到更新

#### Scenario: Batch generate profiles from list
- **WHEN** 用户勾选至少一名教授后点击「批量生成画像」
- **THEN** 为所选教授创建异步科研画像生成任务
- **AND** 任务完成后刷新列表

#### Scenario: University crawl
- **WHEN** 用户点击「院校官网批量添加」
- **THEN** 打开 Modal 选择目标院校
- **AND** 提交后创建异步爬取任务

---

### Requirement: Match Results Page

系统 SHALL 提供匹配结果页面。

#### Scenario: Match results list
- **WHEN** 用户访问 `/match`
- **THEN** 显示当前激活简历的匹配结果
- **AND** 默认按匹配度降序排列
- **AND** 每项显示：排名、教授姓名、机构、匹配度、匹配标签

#### Scenario: Search match results
- **WHEN** 用户在搜索框输入关键词
- **THEN** 按教授姓名模糊搜索匹配结果
- **AND** 搜索时重置到第一页
- **AND** 支持清空搜索恢复完整列表

#### Scenario: Sort match results
- **WHEN** 用户点击教授、机构或匹配度列标题
- **THEN** 按该列升序或降序排列
- **AND** 排序时重置到第一页
- **AND** 显示排序方向指示器

#### Scenario: Run matching
- **WHEN** 用户点击「运行匹配」
- **THEN** 显示 loading 状态
- **AND** 完成后刷新结果列表

#### Scenario: No active profile
- **WHEN** 没有激活的简历
- **THEN** 显示提示：请先激活一份简历

#### Scenario: Match detail
- **WHEN** 用户点击某匹配结果的「详情」
- **THEN** 显示匹配原因分析
- **AND** 显示共同研究方向、技能匹配等

#### Scenario: Generate letter shortcut
- **WHEN** 用户点击匹配结果的「生成邮件」
- **THEN** 为该教授生成联络邮件
- **AND** 跳转到邮件详情

#### Scenario: Export results
- **WHEN** 用户点击「导出 CSV」
- **THEN** 下载包含匹配结果的 CSV 文件
