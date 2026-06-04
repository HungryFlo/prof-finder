## ADDED Requirements

### Requirement: Dark Mode Toggle

系统 SHALL 提供深色模式切换功能。

#### Scenario: Toggle dark mode
- **WHEN** 用户点击 Header 中的深色模式切换按钮
- **THEN** 在 light 和 dark 主题间切换
- **AND** 按钮图标在太阳（light 模式）和月亮（dark 模式）间切换

#### Scenario: Dark mode persistence
- **WHEN** 用户切换深色模式后刷新页面
- **THEN** 主题偏好保持（localStorage）

#### Scenario: Dark mode initialization
- **WHEN** 用户首次访问或 localStorage 无主题偏好
- **THEN** 默认使用 light 模式

#### Scenario: CSS variables in dark mode
- **WHEN** 深色模式激活
- **THEN** HTML root 添加 `.dark` class
- **AND** CSS 变量切换为深色值
- **AND** Naive UI 组件使用 `darkTheme` 渲染

---

## MODIFIED Requirements

### Requirement: Main Layout

系统 SHALL 提供统一的主布局，Header 包含深色模式切换按钮。

#### Scenario: Layout structure
- **WHEN** 用户登录后访问任意页面
- **THEN** 显示主布局：
  - 顶部 Header：Logo、深色模式切换、语言切换、任务面板、用户头像下拉菜单
  - 左侧 Sidebar：导航菜单
  - 主内容区：页面内容
