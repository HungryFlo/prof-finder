# Web 前端规格

## ADDED Requirements

### Requirement: Technology Stack

前端 SHALL 使用以下技术栈构建。

#### Scenario: Core technologies
- **WHEN** 构建前端项目
- **THEN** 使用：
  - Vue 3（Composition API + `<script setup>`）
  - TypeScript
  - Vite
  - Naive UI
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
- **AND** 表格列：姓名、机构、研究方向、论文数、操作
- **AND** 支持分页
- **AND** 支持按机构、研究方向筛选
- **AND** 支持批量选择和删除

#### Scenario: Add by Scholar link
- **WHEN** 用户点击「Scholar 链接添加」
- **THEN** 打开 Modal 输入 Google Scholar URL
- **AND** 提交后爬取信息并添加

#### Scenario: Search Scholar
- **WHEN** 用户点击「搜索 Scholar」
- **THEN** 打开搜索 Modal
- **AND** 输入关键词后显示搜索结果
- **AND** 用户可选择添加

#### Scenario: Add manually
- **WHEN** 用户点击「手动添加」
- **THEN** 打开表单 Modal
- **AND** 填写姓名、机构、研究方向等

#### Scenario: Professor detail
- **WHEN** 用户点击某教授的「查看」
- **THEN** 打开右侧 Drawer
- **AND** 显示教授详情和论文列表

#### Scenario: Refresh professor
- **WHEN** 用户点击「更新」
- **THEN** 重新爬取 Google Scholar 数据

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
