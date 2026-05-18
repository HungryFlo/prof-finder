## ADDED Requirements

### Requirement: Breadcrumb Navigation

系统 SHALL 在主内容区顶部提供面包屑导航。

#### Scenario: Breadcrumb on list pages
- **WHEN** 用户访问列表页面（Profile、Professor、Match、Settings 等）
- **THEN** 页面顶部显示面包屑：首页 > {当前页面名称}
- **AND** 「首页」可点击跳转到 Dashboard
- **AND** 当前页面名称不可点击

#### Scenario: Breadcrumb on detail pages
- **WHEN** 用户访问详情页面（Profile Detail、Professor Detail）
- **THEN** 页面顶部显示面包屑：首页 > {列表页面名称} > {当前项目名称}
- **AND** 「首页」和列表页面名称可点击跳转
- **AND** 当前项目名称不可点击

#### Scenario: Breadcrumb i18n
- **WHEN** 用户切换界面语言
- **THEN** 面包屑标签同步切换语言

#### Scenario: Breadcrumb on Dashboard
- **WHEN** 用户访问 Dashboard 首页
- **THEN** 不显示面包屑（或仅显示不可点击的「首页」）

---

## MODIFIED Requirements

### Requirement: Main Layout

系统 SHALL 提供统一的主布局，主内容区顶部包含面包屑导航。

#### Scenario: Layout structure
- **WHEN** 用户登录后访问任意页面
- **THEN** 显示主布局：
  - 顶部 Header：Logo、深色模式切换、语言切换、任务面板、用户头像下拉菜单
  - 左侧 Sidebar：导航菜单
  - 主内容区顶部：面包屑导航
  - 主内容区：页面内容
