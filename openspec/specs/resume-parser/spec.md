# resume-parser Specification

## Purpose
TBD - created by archiving change add-project-foundation. Update Purpose after archive.
## Requirements
### Requirement: Parser Interface

系统 SHALL 定义统一的简历解析器接口。

#### Scenario: Common interface
- **WHEN** 实现新的简历解析器
- **THEN** 必须实现以下方法：
  - `parse(content: str) -> ParsedResume`: 解析简历内容
  - `supported_extensions() -> List[str]`: 返回支持的文件扩展名

---

### Requirement: Markdown Resume Parser

系统 SHALL 支持解析 Markdown 格式的简历。

#### Scenario: Parse structured markdown
- **WHEN** 输入包含标准标题结构的 Markdown 简历
- **THEN** 提取以下信息：
  - 教育背景（识别 Education, 教育背景, 学历 等标题）
  - 科研经历（识别 Research, 科研经历, 研究经历 等标题）
  - 项目经历（识别 Projects, 项目 等标题）
  - 技能（识别 Skills, 技能, 专长 等标题）

#### Scenario: Parse list items
- **WHEN** Markdown 包含无序/有序列表
- **THEN** 将列表项解析为独立条目

#### Scenario: Handle frontmatter
- **WHEN** Markdown 包含 YAML frontmatter（姓名、邮箱等）
- **THEN** 解析 frontmatter 中的元数据

---

### Requirement: LaTeX Resume Parser

系统 SHALL 支持解析 LaTeX 格式的简历。

#### Scenario: Parse LaTeX structure
- **WHEN** 输入 LaTeX 简历文件
- **THEN** 识别以下结构：
  - `\section{}` 和 `\subsection{}` 作为章节标题
  - `\item` 作为列表项
  - 常见简历宏包格式（如 moderncv, awesome-cv）

#### Scenario: Convert to plain text
- **WHEN** LaTeX 包含复杂命令和环境
- **THEN** 使用 pylatexenc 转换为可读纯文本
- **AND** 保留结构信息用于解析

#### Scenario: Handle Chinese content
- **WHEN** LaTeX 简历包含中文内容
- **THEN** 正确解析中文字符，不乱码

---

### Requirement: Parsed Resume Structure

系统 SHALL 返回标准化的解析结果结构。

#### Scenario: Standard output format
- **WHEN** 任意解析器完成解析
- **THEN** 返回包含以下字段的结构：
  ```
  ParsedResume:
    name: Optional[str]
    education: List[EducationEntry]
      - degree: str (学位)
      - school: str (学校)
      - major: Optional[str] (专业)
      - period: Optional[str] (时间段)
    research_experience: List[ExperienceEntry]
      - title: str (标题/职位)
      - organization: Optional[str] (机构)
      - description: str (描述)
      - period: Optional[str]
    projects: List[ProjectEntry]
      - name: str
      - description: str
    skills: List[str]
    raw_content: str (原始内容)
  ```

---

### Requirement: User Confirmation Flow
系统 SHALL 在 CLI 交互式保存前让用户确认解析结果。

#### Scenario: Display parsed result
- **WHEN** CLI 简历解析完成
- **THEN** 以格式化方式显示提取的信息：
  ```
  === 解析结果 ===

  【教育背景】
  - 本科：清华大学 计算机科学 (2018-2022)
  - 硕士：斯坦福大学 人工智能 (2022-2024)

  【科研经历】
  - NLP研究助理 @ ABC实验室
    发表3篇论文，参与机器翻译项目

  【技能】
  Python, TensorFlow, NLP算法

  是否正确？[Y/n/e(编辑)]
  ```

#### Scenario: User confirms
- **WHEN** 用户输入 Y 或回车
- **THEN** 保存解析结果到数据库

#### Scenario: User edits
- **WHEN** 用户输入 e
- **THEN** 进入交互式编辑模式，允许修改各字段

#### Scenario: User rejects
- **WHEN** 用户输入 n
- **THEN** 取消保存，提示可使用 `profile input` 手动输入

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

### Requirement: Resume Content as Profile Material
The system SHALL preserve resume parsing as one input extraction path for student academic profile generation.

#### Scenario: Resume contributes structured fields
- **WHEN** a supported resume file is included in a student profile material bundle
- **THEN** the resume parser may extract `education`, `research_experience`, `projects`, and `skills`
- **AND** those parsed fields are included as source evidence for the student profile analyzer

#### Scenario: Non-resume material bypasses resume assumptions
- **WHEN** a supported text file is labeled or detected as research interests, personal statement, research plan, or notes
- **THEN** the system does not require that file to fit the resume parser schema
- **AND** the file remains available to the student profile analyzer as raw academic material

### Requirement: Web Background Profile Parsing
Web 简历上传 SHALL 创建后台任务解析简历，并在解析成功后自动保存到简历列表。

#### Scenario: Start web profile parse task
- **WHEN** Web 用户上传 `.md`、`.markdown`、`.tex` 或 `.latex` 简历并提交标题
- **THEN** API 返回 `{task_id, message}` 而不是解析结果预览
- **AND** 前端将该任务加入任务面板

#### Scenario: Auto-save parsed profile
- **WHEN** `profile-parse` 任务解析成功
- **THEN** 系统创建一条 `UserProfile` 记录
- **AND** SSE 完成事件包含新建简历的 `profile_id` 和标题摘要

#### Scenario: Preserve existing active profile
- **WHEN** 用户已有激活简历且 `profile-parse` 任务保存新简历
- **THEN** 新简历保存为未激活状态
- **AND** 原激活简历保持激活

#### Scenario: Activate first parsed profile
- **WHEN** 用户没有激活简历且 `profile-parse` 任务保存新简历
- **THEN** 新简历保存为激活状态

#### Scenario: No confirmation modal
- **WHEN** Web `profile-parse` 任务解析完成
- **THEN** 前端刷新简历列表
- **AND** 不弹出解析结果确认窗口

