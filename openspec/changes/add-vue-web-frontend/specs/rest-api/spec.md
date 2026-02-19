# REST API 规格

## ADDED Requirements

### Requirement: Profile API

系统 SHALL 提供简历管理的 REST API。

#### Scenario: List profiles
- **WHEN** GET `/api/profiles`
- **THEN** 返回当前用户的所有简历列表

#### Scenario: Create profile manually
- **WHEN** POST `/api/profiles` with JSON body
- **THEN** 创建新简历并返回

#### Scenario: Upload profile file
- **WHEN** POST `/api/profiles/upload` with multipart form
- **AND** 文件为 .md 或 .tex 格式
- **THEN** 解析文件内容
- **AND** 返回解析结果（不自动保存，等待用户确认）

#### Scenario: Confirm and save uploaded profile
- **WHEN** POST `/api/profiles` with parsed data and `source: "upload"`
- **THEN** 保存简历到数据库

#### Scenario: Get profile detail
- **WHEN** GET `/api/profiles/{id}`
- **AND** 简历属于当前用户
- **THEN** 返回简历详情

#### Scenario: Update profile
- **WHEN** PUT `/api/profiles/{id}` with JSON body
- **AND** 简历属于当前用户
- **THEN** 更新简历并返回

#### Scenario: Delete profile
- **WHEN** DELETE `/api/profiles/{id}`
- **AND** 简历属于当前用户
- **THEN** 删除简历

#### Scenario: Activate profile
- **WHEN** POST `/api/profiles/{id}/activate`
- **THEN** 将该简历设为激活状态
- **AND** 其他简历设为非激活

#### Scenario: Batch delete profiles
- **WHEN** DELETE `/api/profiles/batch` with `{ "ids": [...] }`
- **THEN** 删除所有指定的简历（仅限当前用户的）

---

### Requirement: Professor API

系统 SHALL 提供教授管理的 REST API。

#### Scenario: List professors
- **WHEN** GET `/api/professors`
- **THEN** 返回当前用户的教授列表
- **AND** 支持分页参数 `?page=1&page_size=20`
- **AND** 支持筛选参数 `?affiliation=xxx&interest=xxx`

#### Scenario: Add professor manually
- **WHEN** POST `/api/professors` with JSON body
- **THEN** 创建教授记录并返回

#### Scenario: Add professor by Scholar link
- **WHEN** POST `/api/professors/scholar` with `{ "url": "..." }`
- **THEN** 爬取 Google Scholar 信息
- **AND** 创建教授记录并返回

#### Scenario: Search Scholar
- **WHEN** POST `/api/professors/search` with `{ "query": "..." }`
- **THEN** 搜索 Google Scholar
- **AND** 返回搜索结果列表（不自动添加）

#### Scenario: Get professor detail
- **WHEN** GET `/api/professors/{id}`
- **THEN** 返回教授详情（含论文列表）

#### Scenario: Update professor
- **WHEN** PUT `/api/professors/{id}` with JSON body
- **THEN** 更新教授信息

#### Scenario: Delete professor
- **WHEN** DELETE `/api/professors/{id}`
- **THEN** 删除教授记录

#### Scenario: Refresh professor data
- **WHEN** POST `/api/professors/{id}/refresh`
- **AND** 教授有 Google Scholar 链接
- **THEN** 重新爬取数据并更新

#### Scenario: Batch delete professors
- **WHEN** DELETE `/api/professors/batch` with `{ "ids": [...] }`
- **THEN** 删除所有指定的教授

---

### Requirement: Match API

系统 SHALL 提供匹配功能的 REST API。

#### Scenario: Run matching
- **WHEN** POST `/api/match/run`
- **AND** 存在激活的简历和教授数据
- **THEN** 执行匹配算法
- **AND** 保存匹配结果
- **AND** 返回匹配结果列表

#### Scenario: Get match results
- **WHEN** GET `/api/match/results`
- **THEN** 返回当前激活简历的匹配结果
- **AND** 按匹配分数降序排列
- **AND** 支持分页和筛选

#### Scenario: Get single match detail
- **WHEN** GET `/api/match/results/{professor_id}`
- **THEN** 返回与该教授的匹配详情
- **AND** 包含匹配原因分析

#### Scenario: No active profile
- **WHEN** POST `/api/match/run`
- **AND** 没有激活的简历
- **THEN** 返回错误：请先激活一份简历

#### Scenario: No professors
- **WHEN** POST `/api/match/run`
- **AND** 没有教授数据
- **THEN** 返回错误：请先添加教授

---

### Requirement: Letter API

系统 SHALL 提供邮件生成的 REST API。

#### Scenario: Generate letter
- **WHEN** POST `/api/letters/generate/{professor_id}`
- **AND** 存在匹配结果
- **THEN** 调用 LLM 生成邮件
- **AND** 保存并返回邮件内容

#### Scenario: Batch generate letters
- **WHEN** POST `/api/letters/batch` with `{ "top": 5 }`
- **THEN** 为 Top N 匹配的教授生成邮件
- **AND** 返回生成结果列表

#### Scenario: List letters
- **WHEN** GET `/api/letters`
- **THEN** 返回所有已生成的邮件列表

#### Scenario: Get letter detail
- **WHEN** GET `/api/letters/{professor_id}`
- **THEN** 返回邮件详情

#### Scenario: Update letter
- **WHEN** PUT `/api/letters/{professor_id}` with `{ "content": "..." }`
- **THEN** 更新邮件内容（用户编辑后保存）

#### Scenario: API key not configured
- **WHEN** 调用生成邮件接口
- **AND** 用户未配置 DeepSeek API Key
- **THEN** 返回错误：请先配置 API Key

---

### Requirement: Settings API

系统 SHALL 提供用户设置的 REST API。

#### Scenario: Get settings
- **WHEN** GET `/api/settings`
- **THEN** 返回当前用户的设置
- **AND** API Key 以脱敏形式返回（仅显示前4位和后4位）

#### Scenario: Update settings
- **WHEN** PUT `/api/settings` with JSON body
- **THEN** 更新用户设置

#### Scenario: Settings fields
- **WHEN** 更新设置
- **THEN** 支持以下字段：
  - `deepseek_api_key`: DeepSeek API Key
  - `deepseek_base_url`: API Base URL
  - `request_delay`: 爬虫请求延时（秒）

---

### Requirement: API Response Format

系统 SHALL 使用统一的 API 响应格式。

#### Scenario: Success response
- **WHEN** API 调用成功
- **THEN** 返回：
  ```json
  {
    "data": { ... },
    "message": "操作成功"
  }
  ```

#### Scenario: Error response
- **WHEN** API 调用失败
- **THEN** 返回：
  ```json
  {
    "error": "错误类型",
    "detail": "详细错误信息"
  }
  ```
- **AND** 使用适当的 HTTP 状态码（400/401/403/404/500）

#### Scenario: Paginated response
- **WHEN** 返回分页数据
- **THEN** 返回：
  ```json
  {
    "data": {
      "items": [...],
      "total": 100,
      "page": 1,
      "page_size": 20,
      "pages": 5
    }
  }
  ```
