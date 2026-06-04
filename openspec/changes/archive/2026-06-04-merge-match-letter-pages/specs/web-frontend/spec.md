## MODIFIED Requirements

### Requirement: Match Results Page

系统 SHALL 提供匹配结果页面，集成邮件查看与编辑功能。

#### Scenario: Match results list
- **WHEN** 用户访问 `/match`
- **THEN** 显示当前激活简历的匹配结果
- **AND** 按匹配度排序
- **AND** 每项显示：排名、教授姓名、机构、匹配度、匹配标签、邮件状态

#### Scenario: Run matching
- **WHEN** 用户点击「运行匹配」
- **THEN** 显示 loading 状态
- **AND** 完成后刷新结果列表

#### Scenario: No active profile
- **WHEN** 没有激活的简历
- **THEN** 显示提示：请先激活一份简历

#### Scenario: Match detail with letter editing
- **WHEN** 用户点击某匹配结果的「详情」
- **THEN** 显示加宽的详情弹窗（900px）
- **AND** 上半部分显示匹配原因分析、研究方向、技能匹配
- **AND** 下半部分显示邮件编辑区域：
  - 若已生成邮件：显示可编辑 textarea 和「复制到剪贴板」「保存邮件」「重新生成」按钮
  - 若未生成邮件：显示「生成邮件」按钮

#### Scenario: Generate letter from detail modal
- **WHEN** 用户在详情弹窗中点击「生成邮件」
- **THEN** 为该教授生成联络邮件
- **AND** 生成完成后在弹窗内显示邮件内容

#### Scenario: Edit and save letter in detail modal
- **WHEN** 用户在详情弹窗中编辑邮件内容并点击「保存邮件」
- **THEN** 保存修改后的邮件内容
- **AND** 显示成功提示

#### Scenario: Copy letter to clipboard
- **WHEN** 用户在详情弹窗中点击「复制到剪贴板」
- **THEN** 将邮件内容复制到剪贴板
- **AND** 显示成功提示

#### Scenario: Export results
- **WHEN** 用户点击「导出 CSV」
- **THEN** 下载包含匹配结果的 CSV 文件

#### Scenario: Letter language selector
- **WHEN** 用户在 Match 页面 header 选择邮件语言（zh/en）
- **THEN** 后续邮件生成使用所选语言
- **AND** 与界面语言（vue-i18n）无关

---

## REMOVED Requirements

### Requirement: Letter Management Page

独立的联络邮件管理页面已被移除，邮件功能整合到匹配结果页面的详情弹窗中。

**Reason:** 匹配结果页和联络邮件页功能高度重叠，合并后减少页面跳转，workflow 更连贯。

**Migration:** 用户通过 Match 页面的详情弹窗查看和编辑邮件。`/letter` 路由重定向到 `/match`。
