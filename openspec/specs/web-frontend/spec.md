# web-frontend Specification

## Purpose

Prof-Finder 的 Web 前端为用户提供登录后的简历、教授、匹配、邮件与设置等能力，并通过 SSE 等机制展示后台任务进度。实现上采用 Vue 3 + Vite + TypeScript，在 Naive UI 的基础上叠加 Tailwind CSS 与 shadcn-vue（Reka UI）组件以支持 AI 聊天等模块，并使用 vue-i18n 提供界面级多语言。
## Requirements
### Requirement: Technology Stack

前端 SHALL 使用以下技术栈构建。

#### Scenario: Core technologies
- **WHEN** 构建前端项目
- **THEN** 使用：
  - Vue 3（Composition API + `<script setup>`）
  - TypeScript
  - Vite
  - Naive UI（主界面）
  - Tailwind CSS 4
  - shadcn-vue / Reka UI（部分现代化与 AI 相关 UI）
  - vue-i18n
  - Pinia
  - Vue Router
  - Axios

---

### Requirement: Authentication Pages

系统 SHALL 提供登录和注册页面。

#### Scenario: Login page
- **WHEN** 用户访问 `/login`
- **THEN** 显示登录表单（用户名、密码）
- **AND** 登录成功后跳转到首页

#### Scenario: Register page
- **WHEN** 用户访问 `/register`
- **THEN** 显示注册表单（用户名、密码、确认密码）
- **AND** 注册成功后跳转到登录页

#### Scenario: Route guard
- **WHEN** 未登录用户访问受保护页面
- **THEN** 自动跳转到登录页
- **AND** 登录后跳回原目标页面

---

### Requirement: Main Layout

系统 SHALL 提供统一的主布局。

#### Scenario: Layout structure
- **WHEN** 用户登录后访问任意页面
- **THEN** 显示主布局：
  - 顶部 Header：Logo、用户头像下拉菜单
  - 左侧 Sidebar：导航菜单
  - 主内容区：页面内容

#### Scenario: Navigation menu
- **WHEN** 显示侧边栏
- **THEN** 包含以下菜单项：
  - 简历管理
  - 教授管理
  - 匹配结果
  - 联络邮件
  - 设置
  - 用户管理（仅管理员可见）

#### Scenario: User dropdown
- **WHEN** 点击用户头像
- **THEN** 显示下拉菜单：设置、登出

---

### Requirement: Profile Management Page

系统 SHALL 提供简历管理页面。

#### Scenario: Profile list
- **WHEN** 用户访问 `/profile`
- **THEN** 显示简历列表表格
- **AND** 表格列：标题、姓名、激活状态、更新时间、操作
- **AND** 支持批量选择和删除

#### Scenario: Upload profile
- **WHEN** 用户点击「上传简历」
- **THEN** 打开上传 Modal
- **AND** 支持拖拽上传 .md/.tex 文件
- **AND** 上传后显示解析结果预览
- **AND** 用户可修改后确认保存

#### Scenario: Create profile manually
- **WHEN** 用户点击「新建简历」
- **THEN** 打开创建 Modal
- **AND** 提供表单输入：标题、姓名、教育背景、科研经历、项目、技能

#### Scenario: Edit profile
- **WHEN** 用户点击某简历的「编辑」
- **THEN** 跳转到 `/profile/{id}`
- **AND** 显示可编辑的简历详情

#### Scenario: Activate profile
- **WHEN** 用户点击「激活」
- **THEN** 将该简历设为激活状态
- **AND** 表格中显示激活标识

#### Scenario: Batch delete
- **WHEN** 用户选择多个简历后点击「批量删除」
- **THEN** 确认后删除所选简历

---

### Requirement: Professor Management Page

系统 SHALL 提供教授管理页面。

#### Scenario: Professor list
- **WHEN** 用户访问 `/professor`
- **THEN** 显示教授列表表格
- **AND** 表格列：姓名（可点击链接）、机构、研究方向（标签）、H-Index、操作
- **AND** 表格行内不得提供「更新」或「画像」按钮
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
- **AND** 按匹配度排序
- **AND** 每项显示：排名、教授姓名、机构、匹配度、匹配标签

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

---

### Requirement: Letter Management Page

系统 SHALL 提供邮件管理页面。

#### Scenario: Letter list
- **WHEN** 用户访问 `/letter`
- **THEN** 显示邮件列表
- **AND** 表格列：教授姓名、状态（已生成/未生成）、生成时间、操作

#### Scenario: Generate letter
- **WHEN** 用户点击「生成」
- **THEN** 调用 LLM 生成邮件
- **AND** 显示 loading 状态
- **AND** 完成后更新列表

#### Scenario: Batch generate
- **WHEN** 用户点击「批量生成」
- **THEN** 打开 Modal 选择 Top N
- **AND** 为前 N 名匹配的教授生成邮件

#### Scenario: Letter detail
- **WHEN** 用户点击「查看」
- **THEN** 打开邮件详情 Modal
- **AND** 显示可编辑的邮件内容
- **AND** 支持「复制」、「保存」操作

#### Scenario: Copy to clipboard
- **WHEN** 用户点击「复制」
- **THEN** 将邮件内容复制到剪贴板
- **AND** 显示成功提示

---

### Requirement: Settings Page

系统 SHALL 提供设置页面。

#### Scenario: Settings sections
- **WHEN** 用户访问 `/settings`
- **THEN** 显示设置页面，包含：
  - 账户设置：修改密码
  - API 配置：DeepSeek API Key、Base URL
  - 爬虫设置：请求延时

#### Scenario: Change password
- **WHEN** 用户填写「当前密码」和「新密码」并提交
- **THEN** 修改密码
- **AND** 显示成功提示

#### Scenario: Update API key
- **WHEN** 用户填写 API Key 并保存
- **THEN** 保存到用户设置
- **AND** 显示脱敏后的 Key

---

### Requirement: Admin User Management

系统 SHALL 为管理员提供用户管理页面。

#### Scenario: User list
- **WHEN** 管理员访问 `/admin/users`
- **THEN** 显示所有用户列表
- **AND** 表格列：用户名、是否管理员、创建时间、操作

#### Scenario: Reset password
- **WHEN** 管理员点击「重置密码」
- **THEN** 打开 Modal 输入新密码
- **AND** 提交后重置该用户密码

#### Scenario: Non-admin access
- **WHEN** 非管理员访问 `/admin/*`
- **THEN** 显示 403 页面或跳转到首页

---

### Requirement: Error Handling

前端 SHALL 优雅处理错误情况。

#### Scenario: API error
- **WHEN** API 返回错误
- **THEN** 显示错误消息（Naive UI Message 组件）

#### Scenario: Network error
- **WHEN** 网络请求失败
- **THEN** 显示网络错误提示

#### Scenario: 401 error
- **WHEN** API 返回 401
- **THEN** 清除 Token
- **AND** 跳转到登录页

#### Scenario: Loading states
- **WHEN** 发起 API 请求
- **THEN** 显示 loading 状态
- **AND** 完成后隐藏 loading

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

### Requirement: Profile AI Chat Panel

The system SHALL provide an embedded chat interface on the profile detail page for AI-guided profile refinement.

#### Scenario: Open chat panel
- **WHEN** the user clicks "AI 优化" on the profile detail page
- **THEN** a chat panel expands below the academic profile section
- **AND** the AI automatically sends an opening question based on profile gaps

#### Scenario: Chat message exchange
- **WHEN** the user types a message and presses send (or Enter)
- **THEN** the message appears in the chat history (right-aligned, user label)
- **AND** a loading indicator shows while waiting for the AI reply
- **AND** the AI reply appears (left-aligned, AI label)
- **AND** the input is cleared for the next message

#### Scenario: Trigger profile refinement
- **WHEN** the user clicks "优化画像" in the chat panel header
- **AND** at least one Q&A exchange has occurred
- **THEN** a loading state shows on the button
- **AND** the refinement API is called with the full chat history
- **AND** on success, the displayed academic profile updates with the refined version
- **AND** a success message is shown

#### Scenario: Refine with no chat history
- **WHEN** the user clicks "优化画像" without any Q&A exchanges
- **THEN** a warning message is shown: "请先与AI进行至少一轮对话"

#### Scenario: Collapse chat panel
- **WHEN** the user clicks the collapse toggle or "AI 优化" button again
- **THEN** the chat panel collapses (chat history preserved in component state while on page)

#### Scenario: Empty profile
- **WHEN** the profile has no `academic_profile` or `profile_analysis`
- **THEN** the AI asks broad discovery questions about the student's background and goals

#### Scenario: Error handling
- **WHEN** the chat API returns an error
- **THEN** an error message is shown in the chat (not as a separate toast)
- **AND** the user can retry sending the message

### Requirement: Internationalization Framework

前端 SHALL 基于 vue-i18n 提供国际化支持。

#### Scenario: Locale files
- **WHEN** 构建前端
- **THEN** 存在 `src/locales/zh.json` 和 `src/locales/en.json` 翻译文件
- **AND** 所有用户可见的 UI 字符串从 locale 文件中获取

#### Scenario: Language switching
- **WHEN** 用户在 Header 点击语言切换按钮
- **THEN** 整个界面语言即时切换
- **AND** Naive UI 组件（日期选择器、分页等）同步切换语言

#### Scenario: Language persistence
- **WHEN** 用户切换语言后刷新页面
- **THEN** 语言选择保留（localStorage）

### Requirement: Letter language selector (independent of UI locale)

套磁信生成 SHALL 由用户在联络邮件或匹配结果界面选择 `zh` 或 `en`，与 vue-i18n 界面语言无关。

#### Scenario: Choose letter language before generate
- **WHEN** 用户点击生成或重新生成套磁信
- **THEN** 请求携带所选 `language`（`zh` 或 `en`）
- **AND** 不与 Header 界面语言开关联动

#### Scenario: Multilingual display names for letters
- **WHEN** 用户在学生画像或教授详情中填写 `name_locales`（中文名/英文名）
- **THEN** 套磁信正文生成时使用当前所选邮件语言对应的姓名字符串
- **IF** 对应语言未填写
- **THEN** 回退到主字段 `name`

### Requirement: Academic content language (English LLM outputs)

学生学术画像、教授科研画像及语义匹配理由等 SHALL 由后端固定生成英文；设置页不再提供「画像生成语言」。

#### Scenario: No profile_language in settings UI
- **WHEN** 用户打开设置页
- **THEN** 不显示「画像生成语言」或 `profile_language` 配置项

### Requirement: Visual design system

The Web frontend SHALL present a cohesive visual system across Naive UI and Tailwind/shadcn surfaces: shared typography, a single accent hue with cool-neutral grays, consistent spacing rhythm, and motion on interactive controls without relying on `window.alert` for validation feedback.

#### Scenario: Typography and readability

- **WHEN** a user views any authenticated or public Vue route
- **THEN** body text uses the same primary font family as Tailwind `font-sans` (no competing default such as Inter alongside Geist)
- **AND** full-viewport shells use `min-height: 100dvh` (or equivalent) instead of `100vh` alone for the root layout where full height is required
- **AND** primary numeric tables or scores MAY use tabular figures (`font-variant-numeric: tabular-nums`) where alignment improves scanability

#### Scenario: Color and surfaces

- **WHEN** the user uses light or dark appearance (including Naive-derived surfaces)
- **THEN** neutral backgrounds and borders belong to one cool-tinted gray family
- **AND** a single accent hue is used for primary actions and key highlights (sidebars SHALL not use a separate high-chroma purple unrelated to that accent)
- **AND** optional subtle grain or noise on the page background MUST NOT intercept pointer events

#### Scenario: Layout rhythm

- **WHEN** the user views the main authenticated layout
- **THEN** main content is constrained with a maximum width and horizontal padding so text and tables do not touch wide-monitor edges
- **AND** vertical spacing between header, alerts, and content follows a clear rhythm (optical asymmetry allowed if documented in implementation notes)

#### Scenario: Interaction and accessibility

- **WHEN** the user navigates with a pointer or keyboard
- **THEN** primary buttons and sidebar navigation items show visible hover, active, and focus-visible affordances within roughly 200–300ms transitions
- **AND** in-page anchor navigation uses smooth scrolling where applicable
- **AND** a skip link is available at the start of the main layout to move focus to the primary content landmark

#### Scenario: Meta and branding

- **WHEN** the app is loaded from `index.html`
- **THEN** the document has a non-empty `meta name="description"`
- **AND** Open Graph `og:title` and `og:description` reflect the product
- **AND** the favicon is not the default Vite logo; it represents Prof-Finder with a simple branded mark

