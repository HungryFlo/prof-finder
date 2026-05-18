## ADDED Requirements

### Requirement: Dashboard Page

系统 SHALL 提供首页仪表盘，展示系统概览和快速操作入口。

#### Scenario: Dashboard display
- **WHEN** 用户访问 `/`（首页）
- **THEN** 显示仪表盘页面，包含：
  - 欢迎区域：显示当前用户名和随机激励话语
  - 统计卡片：Profile 数量、Professor 数量、Match 结果数、已生成 Letter 数
  - 快速操作：创建 Profile、添加 Professor、运行 Match 的快捷按钮
  - 最近活动：最近更新的 Profile 和最近添加的 Professor 各 5 条

#### Scenario: Motivational quotes
- **WHEN** 用户访问 Dashboard
- **THEN** 显示一条随机激励话语
- **AND** 话语随 vue-i18n 语言切换（中文/英文各有 8-10 条）
- **AND** 每次访问随机选择一条

#### Scenario: Quick actions
- **WHEN** 用户点击快速操作中的「创建 Profile」
- **THEN** 跳转到 Profile 管理页面并打开创建 Modal

#### Scenario: Quick action - Add Professor
- **WHEN** 用户点击快速操作中的「添加 Professor」
- **THEN** 跳转到 Professor 管理页面

#### Scenario: Quick action - Run Match
- **WHEN** 用户点击快速操作中的「运行匹配」
- **THEN** 跳转到 Match 结果页面

#### Scenario: Statistics cards
- **WHEN** Dashboard 加载完成
- **THEN** 调用统计 API 获取各项数据
- **AND** 以数字形式展示在统计卡片中
- **AND** 卡片可点击跳转到对应列表页

---

## MODIFIED Requirements

### Requirement: Main Layout

系统 SHALL 提供统一的主布局，首页为 Dashboard。

#### Scenario: Layout structure
- **WHEN** 用户登录后访问任意页面
- **THEN** 显示主布局：
  - 顶部 Header：Logo、用户头像下拉菜单
  - 左侧 Sidebar：导航菜单
  - 主内容区：页面内容

#### Scenario: Navigation menu
- **WHEN** 显示侧边栏
- **THEN** 包含以下菜单项：
  - 首页（Dashboard）
  - 简历管理
  - 教授管理
  - 匹配结果
  - 设置
  - 用户管理（仅管理员可见）

#### Scenario: Default route
- **WHEN** 用户访问 `/`
- **THEN** 显示 Dashboard 页面（不再重定向到 `/profile`）
