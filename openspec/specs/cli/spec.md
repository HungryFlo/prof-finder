# cli Specification

## Purpose
TBD - created by archiving change add-project-foundation. Update Purpose after archive.
## Requirements
### Requirement: Application Entry Point

系统 SHALL 提供名为 `prof-finder` 的命令行入口，支持 `--version` 和 `--help` 选项。

#### Scenario: Show version
- **WHEN** 用户执行 `prof-finder --version`
- **THEN** 显示当前版本号

#### Scenario: Show help
- **WHEN** 用户执行 `prof-finder --help`
- **THEN** 显示所有可用命令和选项的帮助信息

---

### Requirement: Profile Upload Command

系统 SHALL 提供 `profile upload` 命令，允许用户上传简历文件。

#### Scenario: Upload Markdown resume
- **WHEN** 用户执行 `prof-finder profile upload resume.md`
- **THEN** 系统解析 Markdown 文件
- **AND** 显示提取的结构化信息供用户确认
- **AND** 用户确认后保存到数据库

#### Scenario: Upload LaTeX resume
- **WHEN** 用户执行 `prof-finder profile upload resume.tex`
- **THEN** 系统解析 LaTeX 文件
- **AND** 显示提取的结构化信息供用户确认
- **AND** 用户确认后保存到数据库

#### Scenario: Unsupported file format
- **WHEN** 用户上传不支持的文件格式（如 .pdf, .docx）
- **THEN** 显示错误提示："暂不支持该格式，请使用 .md 或 .tex 文件"

---

### Requirement: Profile Input Command

系统 SHALL 提供 `profile input` 命令，允许用户手动输入个人信息。

#### Scenario: Interactive input
- **WHEN** 用户执行 `prof-finder profile input`
- **THEN** 系统依次提示输入：
  - 姓名
  - 教育背景
  - 科研经历
  - 参与项目
  - 技能专长
- **AND** 保存到数据库

#### Scenario: Input with options
- **WHEN** 用户执行 `prof-finder profile input --name "张三" --education "清华大学CS"`
- **THEN** 系统使用提供的选项值，仅提示缺失的字段

---

### Requirement: Profile Show Command

系统 SHALL 提供 `profile show` 命令，显示当前保存的个人简历。

#### Scenario: Show profile
- **WHEN** 用户执行 `prof-finder profile show`
- **AND** 数据库中存在简历数据
- **THEN** 以格式化方式显示完整简历信息

#### Scenario: No profile exists
- **WHEN** 用户执行 `prof-finder profile show`
- **AND** 数据库中无简历数据
- **THEN** 提示："尚未添加简历，请使用 `profile upload` 或 `profile input` 添加"

---

### Requirement: Profile Edit Command

系统 SHALL 提供 `profile edit` 命令，允许编辑已保存的简历。

#### Scenario: Edit specific field
- **WHEN** 用户执行 `prof-finder profile edit --education "新的教育背景"`
- **THEN** 更新指定字段并保存

#### Scenario: Interactive edit
- **WHEN** 用户执行 `prof-finder profile edit`
- **THEN** 显示当前各字段值，允许逐一修改

---

### Requirement: Professor Add Command

系统 SHALL 提供 `professor add` 命令，添加教授信息。

#### Scenario: Add by Google Scholar
- **WHEN** 用户执行 `prof-finder professor add --scholar "https://scholar.google.com/citations?user=xxx"`
- **THEN** 系统从 Google Scholar 爬取教授信息
- **AND** 显示爬取结果供用户确认
- **AND** 保存到数据库

#### Scenario: Add manually
- **WHEN** 用户执行 `prof-finder professor add --name "Dr. Smith" --affiliation "Stanford CS"`
- **THEN** 保存基本信息到数据库
- **AND** 提示用户可补充 Google Scholar 链接以获取更多数据

---

### Requirement: Professor List Command

系统 SHALL 提供 `professor list` 命令，列出所有已添加的教授。

#### Scenario: List professors
- **WHEN** 用户执行 `prof-finder professor list`
- **THEN** 以表格形式显示教授列表（姓名、院系、研究方向摘要）

#### Scenario: Empty list
- **WHEN** 用户执行 `prof-finder professor list`
- **AND** 数据库中无教授数据
- **THEN** 提示："尚未添加教授，请使用 `professor add` 添加"

---

### Requirement: Professor Show Command

系统 SHALL 提供 `professor show` 命令，显示教授详细信息。

#### Scenario: Show professor details
- **WHEN** 用户执行 `prof-finder professor show <id或姓名>`
- **THEN** 显示教授完整信息：姓名、院系、研究方向、论文列表、主页链接

---

### Requirement: Match Command

系统 SHALL 提供 `match` 命令，执行匹配算法。

#### Scenario: Run matching
- **WHEN** 用户执行 `prof-finder match`
- **AND** 存在用户简历和教授数据
- **THEN** 计算匹配分数
- **AND** 按匹配度排序显示教授列表
- **AND** 显示匹配原因（共同研究方向、技能匹配等）

#### Scenario: Missing profile
- **WHEN** 用户执行 `prof-finder match`
- **AND** 无用户简历
- **THEN** 提示："请先添加简历"

#### Scenario: No professors
- **WHEN** 用户执行 `prof-finder match`
- **AND** 无教授数据
- **THEN** 提示："请先添加教授信息"

---

### Requirement: Letter Command

系统 SHALL 提供 `letter` 命令，生成联络邮件。

#### Scenario: Generate letter
- **WHEN** 用户执行 `prof-finder letter <教授id>`
- **THEN** 调用 LLM API 生成个性化联络邮件
- **AND** 显示生成的邮件内容
- **AND** 询问是否保存

#### Scenario: Generate for top matches
- **WHEN** 用户执行 `prof-finder letter --top 5`
- **THEN** 为匹配度最高的5位教授分别生成邮件

#### Scenario: API key not configured
- **WHEN** 用户执行 `prof-finder letter`
- **AND** 未配置 DeepSeek API Key
- **THEN** 提示："请在 .env 文件中配置 DEEPSEEK_API_KEY"

