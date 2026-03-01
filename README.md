# Prof-Finder

**Your Ideal Professor Awaits.** 帮助大学生寻找未来 PhD/MPhil 导师的智能匹配系统。

## 功能特点

- **智能简历解析**：支持 Markdown 和 LaTeX 格式，优先使用 LLM 进行语义理解，自动回退到正则解析
- **教授信息爬取**：通过 Google Scholar 自动获取教授信息、论文和研究方向
- **智能匹配**：基于研究方向、技能和经历进行智能匹配推荐
- **邮件生成**：使用 DeepSeek API 生成个性化的学术联络邮件
- **多用户支持**：每个用户有独立的简历和教授数据库
- **Web 界面**：基于 Vue 3 + Naive UI 的现代 Web 前端

## 快速开始

### 前置要求

- Python 3.9+
- Node.js 18+
- Poetry (Python 包管理)
- Conda (推荐，用于环境管理)

### 安装

```bash
# 克隆项目
git clone https://github.com/your-username/prof-finder.git
cd prof-finder

# 激活 conda 环境
conda activate prof-finder

# 安装后端依赖
poetry install

# 安装前端依赖
cd frontend
npm install
cd ..

# 复制配置文件
cp .env.example .env
# 编辑 .env 文件，填入你的 DeepSeek API Key
```

### 运行

**启动后端 API 服务**

```bash
# 在项目根目录下
uvicorn backend.prof_finder.api.main:app --reload --port 8000
```

**启动前端开发服务器**

```bash
# 在另一个终端
cd frontend
npm run dev
```

然后访问 http://localhost:5173 即可使用 Web 界面。

**默认管理员账号**

- 用户名：`root`
- 密码：`root123`（首次登录需修改）

可通过环境变量 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 自定义。

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

# 管理员账号（可选，默认 root/root123）
ADMIN_USERNAME=root
ADMIN_PASSWORD=root123

# JWT 配置（可选，自动生成）
# JWT_SECRET_KEY=your_secret_key
```

## CLI 使用方法

除了 Web 界面，你也可以使用命令行工具：

### 1. 添加个人简历

```bash
# 上传 Markdown 简历（默认使用 LLM 智能解析）
prof-finder profile upload resume.md --title "NLP方向申请"

# 上传 LaTeX 简历
prof-finder profile upload cv.tex --title "ML方向申请"

# 禁用 LLM 解析，仅使用正则解析
prof-finder profile upload resume.md --no-llm
```

### 2. 添加教授

```bash
# 通过 Google Scholar 链接添加
prof-finder professor add --scholar "https://scholar.google.com/citations?user=xxx"

# 搜索教授
prof-finder professor search "Andrew Ng"
```

### 3. 执行匹配

```bash
prof-finder match run
prof-finder match show --top 10
```

### 4. 生成联络邮件

```bash
prof-finder letter generate <professor_id>
prof-finder letter batch --top 5
```

## 项目结构

```
prof-finder/
├── backend/                 # 后端代码
│   ├── prof_finder/
│   │   ├── api/             # FastAPI REST API
│   │   ├── cli/             # 命令行接口
│   │   ├── parser/          # 简历解析器
│   │   ├── crawler/         # 网页爬虫
│   │   ├── matcher/         # 匹配算法
│   │   ├── llm/             # LLM 集成
│   │   ├── models/          # 数据模型
│   │   └── db/              # 数据库操作
│   └── tests/               # 后端测试
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── api/             # API 请求
│   │   ├── components/      # Vue 组件
│   │   ├── layouts/         # 布局组件
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态
│   │   ├── types/           # TypeScript 类型
│   │   └── views/           # 页面组件
│   └── package.json
├── openspec/                # 项目规格文档
├── pyproject.toml           # Python 项目配置
└── README.md
```

## 开发

### 开发环境准备

```bash
# 创建并激活 conda 环境（首次）
conda create -n prof-finder python=3.9+
conda activate prof-finder

# 安装依赖
poetry install
cd frontend && npm install && cd ..

# 复制环境变量
cp .env.example .env
# 编辑 .env，至少设置 DEEPSEEK_API_KEY
```

### 常用命令

```bash
# 运行后端测试
python -m pytest backend/tests/ -v

# 代码格式化
black backend/

# 类型检查
mypy backend/

# 前端开发
cd frontend
npm run dev

# 前端构建
npm run build
```

### 本地联调

同时启动后端和前端进行开发：

```bash
# 终端 1：后端
uvicorn backend.prof_finder.api.main:app --reload --port 8000

# 终端 2：前端
cd frontend && npm run dev
```

前端默认代理 `/api` 到 `http://localhost:8000`，无需额外配置。

## API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License

# 现在还有一大堆问题

1. 不能同时激活两份简历
2. 匹配算法中文对中文，准确率太低了
3. 生成邮件要选择中英文，现在的prompt也很烂
4. 学校的网站维护太烂了，根本爬取不到什么信息

# 但是还可以先优化其他方向

## 增进对教授的了解

在教授信息的修改页面能够继续进行信息的自动化爬取和补充：

上传该教授的文章的pdf版本让大模型进行总结，完善大模型的prompt

教师个人主页手动添加之后通过网页源代码来总结教师的特点和信息。

## 增进对使用者的了解

上传使用者的其他资料，包括个人主页（可以和教师个人主页的解析功能进行复用）、论文（可以和教师的论文阅读功能进行复用）

## 改进匹配算法

先进行语言的统一再进行相似度计算？

使用多维度匹配，而不是捕风捉影，包括：研究方向相似度、