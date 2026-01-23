# Resume Parser Specification - Delta

## ADDED Requirements

### Requirement: LLM Resume Parser

系统 SHALL 支持使用 LLM API 解析简历内容。

#### Scenario: LLM parsing success
- **WHEN** 用户上传简历文件
- **AND** DeepSeek API 可用
- **THEN** 使用 LLM 提取结构化信息
- **AND** 返回 `ParsedResume` 对象

#### Scenario: LLM parsing with context
- **WHEN** 简历包含复杂或非标准格式
- **THEN** LLM 能够理解语义上下文
- **AND** 正确区分不同类型的经历（研究/教学/实习等）

#### Scenario: JSON output format
- **WHEN** LLM 解析完成
- **THEN** 返回符合以下结构的 JSON：
  ```json
  {
    "name": "string",
    "education": [{"degree": "string", "school": "string", "major": "string?", "period": "string?"}],
    "research_experience": [{"title": "string", "organization": "string?", "description": "string", "period": "string?"}],
    "projects": [{"name": "string", "description": "string"}],
    "skills": ["string"]
  }
  ```

---

### Requirement: Prompt Management

系统 SHALL 统一管理所有 LLM prompt 模板。

#### Scenario: Load prompt from YAML
- **WHEN** 需要使用 prompt
- **THEN** 从 `src/prof_finder/prompts/` 目录加载对应 YAML 文件
- **AND** 支持变量替换（如 `{content}` 替换为实际内容）

#### Scenario: Prompt structure
- **WHEN** 定义 prompt 模板
- **THEN** YAML 文件包含以下结构：
  ```yaml
  prompt_name:
    system: "系统提示词"
    user: "用户提示词模板，支持 {variable} 占位符"
  ```

---

### Requirement: Smart Parser with Fallback

系统 SHALL 提供智能解析器，自动选择最佳解析方式。

#### Scenario: LLM first strategy
- **WHEN** 用户上传简历
- **THEN** 优先尝试 LLM 解析
- **IF** LLM 解析成功
- **THEN** 返回 LLM 解析结果

#### Scenario: Fallback to regex
- **WHEN** LLM 解析失败（网络错误、API 限流、JSON 解析失败）
- **THEN** 自动回退到正则表达式解析器
- **AND** 根据文件扩展名选择对应的正则解析器（LaTeX/Markdown）

#### Scenario: Both parsers fail
- **WHEN** LLM 和正则解析器都无法提取有效信息
- **THEN** 返回空结果
- **AND** 提示用户使用 `profile input` 手动输入

#### Scenario: Parsing method indication
- **WHEN** 解析完成
- **THEN** CLI 显示使用的解析方式（LLM/正则）
- **AND** 显示格式：`[cyan]使用 LLM 解析成功[/cyan]` 或 `[yellow]回退到正则解析[/yellow]`

---

## MODIFIED Requirements

### Requirement: Error Handling

系统 SHALL 优雅处理解析错误。

#### Scenario: Empty file
- **WHEN** 上传的文件为空
- **THEN** 提示："文件内容为空，请检查文件"

#### Scenario: Parse failure
- **WHEN** 无法从文件中提取任何有效信息（LLM 和正则都失败）
- **THEN** 提示："无法自动解析简历，建议使用 `profile input` 手动输入"
- **AND** 提供将原始内容保存的选项

#### Scenario: Partial parse
- **WHEN** 仅部分字段成功提取
- **THEN** 显示已提取的信息
- **AND** 标注哪些字段未能识别
- **AND** 允许用户补充缺失信息

#### Scenario: LLM API error
- **WHEN** DeepSeek API 返回错误（网络超时、限流、认证失败）
- **THEN** 记录错误日志
- **AND** 自动回退到正则解析
- **AND** 不向用户显示 API 错误详情（除非开启 debug 模式）

#### Scenario: LLM response invalid
- **WHEN** LLM 返回的 JSON 格式无效或结构不符合预期
- **THEN** 尝试修复 JSON（如移除多余字符）
- **IF** 修复失败
- **THEN** 回退到正则解析
