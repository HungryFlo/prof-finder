# Resume Parser Specification

## ADDED Requirements

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

系统 SHALL 在保存前让用户确认解析结果。

#### Scenario: Display parsed result
- **WHEN** 简历解析完成
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

---

### Requirement: Error Handling

系统 SHALL 优雅处理解析错误。

#### Scenario: Empty file
- **WHEN** 上传的文件为空
- **THEN** 提示："文件内容为空，请检查文件"

#### Scenario: Parse failure
- **WHEN** 无法从文件中提取任何有效信息
- **THEN** 提示："无法自动解析简历，建议使用 `profile input` 手动输入"
- **AND** 提供将原始内容保存的选项

#### Scenario: Partial parse
- **WHEN** 仅部分字段成功提取
- **THEN** 显示已提取的信息
- **AND** 标注哪些字段未能识别
- **AND** 允许用户补充缺失信息
