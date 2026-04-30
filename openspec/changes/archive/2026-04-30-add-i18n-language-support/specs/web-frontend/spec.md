## ADDED Requirements
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

### Requirement: Content Language Selector

系统 SHALL 在画像生成页面提供内容语言选择器。

#### Scenario: Language toggle on profile detail
- **WHEN** 用户查看学生画像详情页
- **THEN** 显示语言切换按钮（中文/English）
- **AND** 选择后影响「AI 优化」和「优化画像」生成的输出语言

#### Scenario: Language toggle on professor detail
- **WHEN** 用户查看教授详情页
- **THEN** 显示语言切换按钮（中文/English）
- **AND** 选择后影响「生成科研画像」和「论文总结」的输出语言

#### Scenario: Language matches user default
- **WHEN** 页面首次加载
- **THEN** 内容语言选择器默认显示用户在设置中的 `profile_language` 偏好
