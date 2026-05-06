## MODIFIED Requirements

### Requirement: Settings Page

系统 SHALL 提供设置页面。

#### Scenario: Settings sections
- **WHEN** 用户访问 `/settings`
- **THEN** 显示设置页面，包含：
  - 账户设置：修改密码
  - API 配置：DeepSeek API Key、Base URL
  - 爬虫设置：请求延时
  - 教授数据：添加或从 Scholar 同步后自动执行的 enrichment 子步开关（出版物详情、论文摘要、科研画像）

#### Scenario: Change password
- **WHEN** 用户填写「当前密码」和「新密码」并提交
- **THEN** 修改密码
- **AND** 显示成功提示

#### Scenario: Update API key
- **WHEN** 用户填写 API Key 并保存
- **THEN** 保存到用户设置
- **AND** 显示脱敏后的 Key

#### Scenario: Update auto-enrichment toggles
- **WHEN** 用户切换自动 enrichment 子步开关并保存
- **THEN** 将对应布尔值写入用户设置
- **AND** 后续添加/同步教授行为遵循新配置
