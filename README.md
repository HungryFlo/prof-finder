# Prof-Finder

**Your Ideal Professor Awaits.** 帮助大学生寻找未来 PhD/MPhil 导师的智能匹配系统。

## 功能特点

- **智能简历解析**：支持 Markdown 和 LaTeX 格式，优先使用 LLM 进行语义理解，自动回退到正则解析
- **教授信息爬取**：通过 Google Scholar 自动获取教授信息、论文和研究方向
- **智能匹配**：基于研究方向、技能和经历进行智能匹配推荐
- **邮件生成**：使用 DeepSeek API 生成个性化的学术联络邮件
- **多用户支持**：每个用户有独立的简历和教授数据库

## 安装

### 前置要求

- Python 3.9+
- Poetry (推荐) 或 pip

### 使用 Poetry 安装

```bash
# 克隆项目
git clone https://github.com/your-username/prof-finder.git
cd prof-finder

# 激活 conda 环境
conda activate prof-finder

# 安装依赖
poetry install

# 复制配置文件
cp .env.example .env
# 编辑 .env 文件，填入你的 DeepSeek API Key
```

### 使用 pip 安装

```bash
pip install -e .
```

## 配置

编辑 `.env` 文件：

```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 数据库路径
DATABASE_PATH=./data/prof_finder.db

# 爬虫配置
REQUEST_DELAY=3  # 请求间隔（秒），避免被封

# 默认用户名
DEFAULT_USER=default
```

## 使用方法

### 1. 添加个人简历

**方式一：上传简历文件**

```bash
# 上传 Markdown 简历（默认使用 LLM 智能解析）
prof-finder profile upload resume.md --title "NLP方向申请"

# 上传 LaTeX 简历
prof-finder profile upload cv.tex --title "ML方向申请"

# 禁用 LLM 解析，仅使用正则解析
prof-finder profile upload resume.md --no-llm
```

> **注意**：LLM 解析需要配置 DeepSeek API Key。如果 API 调用失败，系统会自动回退到正则解析。

**方式二：手动输入**

```bash
prof-finder profile input --title "我的简历"
# 然后按提示输入教育背景、科研经历、技能等
```

### 2. 管理简历

```bash
# 查看当前激活的简历
prof-finder profile show

# 列出所有简历
prof-finder profile list

# 切换激活的简历
prof-finder profile activate <profile_id>
```

### 3. 添加教授

```bash
# 通过 Google Scholar 链接添加
prof-finder professor add --scholar "https://scholar.google.com/citations?user=JicYPdAAAAAJ"

# 搜索教授
prof-finder professor search "Andrew Ng"

# 手动添加（稍后可补充 Scholar 信息）
prof-finder professor add --name "Dr. Smith" --affiliation "Stanford CS"
```

### 4. 管理教授

```bash
# 列出所有教授
prof-finder professor list

# 查看教授详情（包含论文）
prof-finder professor show <professor_id> --publications

# 更新教授信息
prof-finder professor update <professor_id>
```

### 5. 执行匹配

```bash
# 运行匹配算法
prof-finder match run

# 查看匹配结果
prof-finder match show --top 10
```

### 6. 生成联络邮件

```bash
# 为特定教授生成邮件
prof-finder letter generate <professor_id>

# 为 Top N 匹配的教授批量生成
prof-finder letter batch --top 5

# 查看已生成的邮件
prof-finder letter show <professor_id>
```

### 多用户使用

```bash
# 为特定用户操作
prof-finder profile list --user alice
prof-finder professor add --scholar "..." --user alice
```

## 项目结构

```
prof-finder/
├── src/prof_finder/
│   ├── cli/            # 命令行接口
│   ├── parser/         # 简历解析器（含 LLM 和正则解析）
│   ├── prompts/        # LLM Prompt 模板
│   ├── crawler/        # 网页爬虫
│   ├── matcher/        # 匹配算法
│   ├── llm/            # LLM 集成（邮件生成）
│   ├── models/         # 数据模型
│   └── db/             # 数据库操作
├── tests/              # 测试用例
├── data/               # 数据存储
├── openspec/           # 项目规格文档
└── pyproject.toml      # 项目配置
```

## 开发

```bash
# 运行测试
pytest

# 代码格式化
black src/

# 类型检查
mypy src/
```

## License

MIT License
