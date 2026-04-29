## ADDED Requirements

### Requirement: Professor Edit Page

系统 SHALL 提供教授信息编辑界面，支持手动编辑、PDF 上传、ArXiv 链接输入三种方式。

#### Scenario: Open edit page
- **WHEN** 用户在教授管理页点击“编辑”
- **THEN** 跳转到 `/professor/{id}/edit`（或等效编辑视图）
- **AND** 加载该教授当前信息

#### Scenario: Edit professor manually
- **WHEN** 用户修改姓名、机构、研究方向、论文、备注等字段
- **THEN** 前端进行基础校验并允许提交手动修改

#### Scenario: Upload PDF for enrichment
- **WHEN** 用户在编辑页上传 PDF
- **THEN** 前端调用来源输入 API 创建 PDF SourceInput
- **AND** 展示提取状态与内容预览

#### Scenario: Submit ArXiv link for enrichment
- **WHEN** 用户在编辑页输入 ArXiv 链接并提交
- **THEN** 前端调用来源输入 API 创建 ArXiv SourceInput
- **AND** 展示返回的元数据预览

#### Scenario: ArXiv metadata-only fallback
- **WHEN** ArXiv 元数据获取成功但 PDF 下载/解析失败
- **THEN** 前端显示“已保存元数据，稍后可重试 PDF 解析”的提示
- **AND** 仍允许用户继续编辑并使用元数据

#### Scenario: Retry ArXiv PDF parsing from UI
- **WHEN** 某 ArXiv SourceInput 处于仅元数据状态
- **THEN** 前端提供“重试 PDF 解析”操作
- **AND** 调用重试接口后刷新该来源的解析状态与预览

#### Scenario: Preview then apply
- **WHEN** 用户完成手动编辑与来源输入选择后点击“预览变更”
- **THEN** 前端展示候选变更对比
- **AND** 用户确认后才提交“应用变更”

#### Scenario: Display paper summaries in professor detail
- **WHEN** 教授详情中存在 `paper_summaries`
- **THEN** 前端新增“论文总结”区块展示摘要内容
- **AND** 显示总结关键词标签，便于后续人工修订

---

### Requirement: Reusable Source Input Component

系统 SHALL 提供可复用的 Source Input 组件，用于承载 PDF 与 ArXiv 输入交互。

#### Scenario: Component reuse in professor editing
- **WHEN** 教授编辑页面需要来源输入能力
- **THEN** 使用统一 Source Input 组件，而非页面内重复实现

#### Scenario: Component ready for profile editing
- **WHEN** 未来实现个人信息修改页面
- **THEN** 可直接复用同一 Source Input 组件
- **AND** 仅需接入不同实体的保存 API
