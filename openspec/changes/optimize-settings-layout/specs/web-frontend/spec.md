## MODIFIED Requirements

### Requirement: Settings Page

系统 SHALL 提供设置页面，使用网格布局优化空间利用。

#### Scenario: Settings layout
- **WHEN** 用户访问 `/settings`
- **THEN** 显示设置页面：
  - 上半部分：API 配置卡片和自动化设置卡片并排显示（2 列网格布局）
  - 下半部分：修改密码卡片全宽显示
- **AND** 窄屏（< 900px）时自动回退为单列堆叠

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
