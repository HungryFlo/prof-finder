## ADDED Requirements

### Requirement: Dashboard API

系统 SHALL 提供 Dashboard 数据聚合 API。

#### Scenario: Get dashboard statistics
- **WHEN** GET `/api/dashboard/stats`
- **AND** 用户已认证
- **THEN** 返回当前用户的统计数据：
  - `profile_count`: 简历数量
  - `professor_count`: 教授数量
  - `match_count`: 匹配结果数量
  - `letter_count`: 已生成邮件数量

#### Scenario: Get recent activity
- **WHEN** GET `/api/dashboard/recent`
- **AND** 用户已认证
- **THEN** 返回最近活动数据：
  - `recent_profiles`: 最近更新的 5 条简历（id, title, updated_at）
  - `recent_professors`: 最近添加的 5 条教授（id, name, affiliation, created_at）
