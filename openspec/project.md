# Project Context

## Purpose

**Prof-Finder** 是一个帮助大学生（本科生、硕士生）寻找未来 PhD 或 MPhil 导师的智能匹配系统。

核心价值：
- 自动化教授信息收集与整理
- 基于个人背景的智能匹配推荐
- AI驱动的个性化学术联络邮件生成
- 提高学生与潜在导师的匹配效率

项目定位：
- 开源工具，供个人部署使用
- **CLI 与 Web 双入口**：命令行适合脚本与自动化；Web 界面（Vue 3 + FastAPI）提供完整交互与任务面板

## Tech Stack

### Core Technologies
- **Backend Framework**: FastAPI
- **Database**: SQLite (轻量级持久化存储)
- **CLI Framework**: Typer
- **Web Scraping**: 
  - BeautifulSoup4 (HTML解析)
  - Requests (HTTP客户端)
  - Scholarly (Google Scholar数据抓取，pip install)
- **LLM Integration**: DeepSeek API
- **Semantic Matching**: `sentence-transformers` + `Qwen/Qwen3-Embedding-0.6B`（首次经 [ModelScope](https://www.modelscope.cn) 下载至本地 `models/qwen3-embedding-0.6b`）
- **Task Queue**: Huey (`SqliteHuey`，队列库默认 `data/huey_tasks.db`）
- **Environment Management**: python-dotenv

### Data Processing
- **Resume Parsing**: 
  - LaTeX: pylatexenc, regex
  - Markdown: markdown-it-py, frontmatter
- **Text Processing**: NLTK 或 spaCy (可选，用于关键词提取)

### Development Tools
- **Dependency Management**: Poetry
- **Code Quality**: 
  - black (代码格式化)
  - flake8 (linting)
  - mypy (类型检查)
- **Testing**: pytest

### Frontend (已实现)
- **Framework**: Vue 3 + TypeScript + Vite
- **UI**: Naive UI（主界面组件）；**Tailwind CSS 4** + **shadcn-vue**（基于 Reka UI）用于部分 AI 聊天与现代化组件
- **i18n**: vue-i18n（界面中英文等）
- **State**: Pinia
- **Router**: Vue Router
- **HTTP**: Axios

### Future Considerations
- **Advanced Scraping**: Playwright/Selenium (处理JS渲染页面)

## Project Conventions

在运行任何python代码以及安装任何python包之前，必须conda activate prof-finder

### Code Style

**Python Style Guide**
- 遵循 PEP 8 规范
- 使用 Black 进行自动格式化（line-length=100）
- 使用类型注解（Type Hints）
- 文档字符串采用 Google Style

**命名约定**
- 文件/模块: `snake_case.py`
- 类名: `PascalCase`
- 函数/变量: `snake_case`
- 常量: `UPPER_SNAKE_CASE`
- 私有成员: `_leading_underscore`

**项目结构**
```
prof-finder/
├── backend/              # 后端代码
│   ├── prof_finder/
│   │   ├── api/          # FastAPI REST API
│   │   ├── cli/          # 命令行界面
│   │   ├── crawler/      # 网页爬虫模块（含 universities 学校适配）
│   │   ├── parser/       # 简历解析模块
│   │   ├── matcher/      # 匹配算法模块
│   │   ├── llm/          # LLM集成模块
│   │   ├── ai_workflows/ # AI 工作流编排
│   │   ├── prompts/      # LLM 提示词与 YAML 配置
│   │   ├── db/           # 数据库操作
│   │   └── models/       # 数据模型
│   └── tests/            # 后端测试
├── frontend/             # Vue 3 前端
│   ├── src/
│   │   ├── api/          # API 请求
│   │   ├── components/    # Vue 组件
│   │   ├── layouts/      # 布局组件
│   │   ├── router/       # 路由配置
│   │   ├── stores/       # Pinia 状态
│   │   ├── types/        # TypeScript 类型
│   │   └── views/        # 页面组件
│   └── package.json
├── openspec/             # OpenSpec 规格文档
├── data/                 # 数据存储目录
├── .env.example          # 环境变量模板
├── pyproject.toml        # 项目配置
└── README.md
```

### Architecture Patterns

**分层架构**
1. **CLI Layer**: 用户交互入口
2. **Service Layer**: 业务逻辑（爬取、解析、匹配、生成）
3. **Data Layer**: 数据库访问与模型
4. **External Integration**: 第三方API/服务

**设计原则**
- 单一职责：每个模块专注一个功能
- 依赖注入：便于测试和模块替换
- 配置外部化：敏感信息通过环境变量管理
- 错误优雅处理：网络请求失败、API限流等场景

**数据流**
```
用户输入 → 解析/爬取 → 数据库存储 → 匹配算法 → LLM生成 → 结果输出
```

### Testing Strategy

**测试层级**
- **Unit Tests**: 覆盖核心业务逻辑（解析器、匹配器）
- **Integration Tests**: 数据库操作、API调用
- **E2E Tests**: CLI命令完整流程（可选）

**Mock策略**
- 外部API调用（DeepSeek、Scholarly）使用Mock
- 文件系统操作使用临时目录
- 数据库测试使用内存SQLite（`:memory:`）

**覆盖率目标**
- 核心模块 >80%
- 工具函数 >60%

### Git Workflow

**分支策略**
- `main`: 稳定版本
- `develop`: 开发分支（可选）
- `feature/*`: 新功能开发
- `fix/*`: Bug修复

**提交规范**
遵循 Conventional Commits:
- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具配置

**示例**
```
feat: add resume parser for LaTeX format
fix: handle network timeout in crawler
docs: update README with installation steps
```

## Domain Context

### 学术场景知识

**教授信息来源**
- 大学官方教师列表页面（结构化程度高）
- Google Scholar个人主页（论文、引用数据）
- 个人学术主页（研究兴趣、招生信息）

**匹配维度**
- **研究方向匹配**: 关键词重合度（NLP、Computer Vision等）
- **学术产出**: 论文数量、影响力（引用数）
- **学生背景**: 教育经历、科研经历、技能专长
- **招生状态**: 是否明确表示招生（网页爬取或手动标注）

**联络信生成要点**
- 展示对教授研究的了解（引用具体论文）
- 突出学生相关背景与匹配点
- 礼貌正式、简洁清晰（300-500字）
- 避免模板化、千篇一律

### 爬虫适配策略

**挑战**
- 每个大学的教师页面结构不同（CSS选择器、HTML结构）
- 需要针对不同学校编写适配器

**解决方案（可扩展设计）**
- 插件化适配器：每个大学一个适配器类
- 配置文件驱动：YAML/JSON定义CSS选择器规则
- 通用提取器：尝试启发式方法提取姓名、邮箱、链接
- 用户辅助：允许用户手动输入教授列表

**Google Scholar**
- 使用scholarly库
- 注意反爬虫策略（延时、代理、随机User-Agent）
- 缓存数据减少重复请求

## Important Constraints

### Technical Constraints
1. **网络依赖**: 爬虫和API调用需要稳定网络
2. **API限流**: DeepSeek API可能有速率限制，需实现重试机制
3. **反爬虫**: Google Scholar、大学网站可能有访问限制
4. **数据准确性**: 网页结构变化可能导致爬取失败，需要错误处理

### Performance Constraints
- 爬取速度：控制请求频率避免被封IP（建议2-5秒/请求）
- 批量处理：一次处理大量教授时显示进度条
- 数据库查询：SQLite对于个人使用足够，但大规模数据需优化索引

### Usability Constraints
- 用户确认机制：简历解析后展示结果让用户确认/修改
- 错误提示友好：网络失败、API错误需清晰提示
- 配置简单：`.env`文件配置API密钥，无需复杂配置

### Legal/Ethical Constraints
- **数据使用**: 爬取的教授信息仅供个人匹配使用，不得用于商业目的
- **隐私保护**: 不公开存储或分享教授个人信息
- **邮件生成**: AI生成的邮件需用户审阅后发送，避免spam

## External Dependencies

### APIs & Services

**DeepSeek API**
- 用途: 生成个性化联络邮件
- 配置: 需要API Key（通过`.env`文件）
- 文档: https://platform.deepseek.com/docs
- 备选方案: 支持OpenAI API兼容接口（便于切换模型）

**Google Scholar (Scholarly)**
- 用途: 获取教授论文、引用数据
- 集成方式: PyPI `scholarly` 包（见 `pyproject.toml`）
- 注意事项: 可能需要代理或延时避免被限制；用户须自行遵守 Google 与各站点服务条款

**DBLP**
- 用途: 稳定的 CS 论文书目与作者主页数据
- 集成方式: 公开 API / 作者 PID 页面

**语义嵌入模型（Qwen3-Embedding-0.6B）**
- 用途: 学生画像与教授之间的向量相似度匹配
- 下载: `modelscope.snapshot_download("Qwen/Qwen3-Embedding-0.6B")` 至数据目录下 `models/qwen3-embedding-0.6b`
- 体积: 约 1.2 GB（因版本与缓存而异，以实际下载为准）
- 自检: `python scripts/check_modelscope.py` 或 `bash scripts/check_modelscope.sh`

### External Data Sources
- **大学官网**: 教授列表页面（用户提供URL）
- **学术主页**: 教授个人网站（从列表页爬取）
- **Google Scholar**: 论文与引用数据

### Configuration Files

**.env（不提交到Git）**
```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DATABASE_PATH=./data/prof_finder.db
SCHOLARLY_PROXY=  # 可选，爬虫代理
REQUEST_DELAY=3   # 爬取延时（秒）
```

**.env.example（提交到Git）**
```bash
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DATABASE_PATH=./data/prof_finder.db
SCHOLARLY_PROXY=
REQUEST_DELAY=3
ADMIN_USERNAME=root
ADMIN_PASSWORD=root123
JWT_SECRET_KEY=your_stable_secret_here
```

### Legal and Responsible Use

- 爬虫与第三方数据（Google Scholar、院校网站、DBLP 等）仅供个人学术申请辅助；部署者须遵守各平台 ToS、版权与 robots 规则，并合理设置 `REQUEST_DELAY`。
- LLM 生成的套磁信与画像内容仅供参考，发送前须人工审阅；项目作者不对滥用爬取或误导性邮件承担责任。

## Extensibility Considerations

### 第一版（MVP）范围
- ✅ 支持LaTeX/Markdown简历解析
- ✅ Google Scholar / DBLP 教授信息获取
- ✅ 基于 Qwen3 嵌入的语义匹配（向量余弦相似度 + 教授嵌入缓存）
- ✅ DeepSeek API生成联络邮件
- ✅ CLI命令行交互
- ✅ SQLite本地存储
- ✅ Web 前端界面（Vue 3 + FastAPI REST API）
- ✅ 多用户认证（JWT）
- ✅ 后台任务面板（SSE 进度推送）
- ✅ 前端界面多语言（vue-i18n，如中英切换）

### 后续扩展方向
- 🔄 更多大学官网爬虫适配器（插件化设计）
- 🔄 匹配链路增强（rerank、多信号融合等）
- 🔄 支持PDF/DOCX简历格式
- 🔄 批量导出联络邮件（Markdown/PDF）
- 🔄 教授数据定期更新机制
- 🔄 邮件内容多语言模板（与界面语言策略对齐）

## Success Metrics

### 功能完整性
- 用户能完成从简历输入到邮件生成的完整流程
- 系统能处理至少50位教授的数据爬取与匹配

### 数据质量
- 简历解析准确率 >85%（用户确认机制）
- 匹配结果Top 10包含用户认可的导师（主观评估）

### 用户体验
- CLI命令易于理解，错误提示清晰
- 单次完整流程耗时 <10分钟（不含大量爬取）

### 代码质量
- 核心模块测试覆盖率 >80%
- 文档完整（README、API文档、代码注释）
