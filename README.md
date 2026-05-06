# Prof-Finder

**Your Ideal Professor Awaits.** 帮助大学生寻找未来 PhD/MPhil 导师的智能匹配系统。

## 功能特点

- **智能简历解析**：支持 Markdown 和 LaTeX 格式，优先使用 LLM 进行语义理解，自动回退到正则解析
- **教授信息爬取**：通过 Google Scholar 自动获取教授信息、论文和研究方向
- **智能匹配**：基于研究方向、技能和经历进行智能匹配推荐
- **邮件生成**：使用 DeepSeek API 生成个性化的学术联络邮件
- **多用户支持**：每个用户有独立的简历和教授数据库
- **Web 界面**：Vue 3 + TypeScript + Vite；界面层使用 Naive UI，并配合 Tailwind CSS、shadcn-vue（Reka UI）、vue-i18n 等

## 快速开始

### 方式一：下载便携版（推荐给普通用户）

在 GitHub Releases 下载与你系统匹配的便携包：

- Windows: `Prof-Finder-windows-x64.zip`
- macOS Apple Silicon: `Prof-Finder-macos-arm64.zip`
- Linux: `Prof-Finder-linux-x64.tar.gz`

解压后双击或运行 `Prof-Finder` / `Prof-Finder.exe`。应用会在本机启动服务，并自动打开系统浏览器。

便携版不要求用户安装 Python、Node.js、Poetry 或 npm。首次登录后请先修改默认管理员密码，并在「设置」中填写 DeepSeek API Key。

默认管理员账号：

- 用户名：`root`
- 密码：`root123`（首次登录需修改）

便携版会把数据库、任务队列、日志和运行时配置保存到系统用户数据目录，而不是解压目录。

如需卸载并彻底清理数据，请先关闭正在运行的 Prof-Finder，再运行便携包内的卸载脚本：

- Windows: `uninstall-prof-finder.bat`
- macOS / Linux: `./uninstall-prof-finder.sh`

卸载脚本会要求输入 `DELETE` 确认，然后删除 Prof-Finder 用户数据目录，并尽可能删除当前解压出来的便携包目录。该操作不可恢复。

### 方式二：开发环境运行

### 前置要求

- Python 3.10+（与 `pyproject.toml` 中 `>=3.10,<4.0` 一致）
- Node.js **20.19+** 或 **22.12+**（见 `frontend/package.json` 的 `engines`）
- Poetry (Python 包管理)
- Conda (推荐，用于环境管理)

### 安装

```bash
# 克隆项目
git clone https://github.com/HungryFlo/prof-finder.git
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
│   │   ├── ai_workflows/    # AI 工作流（画像生成等）
│   │   ├── parser/          # 简历解析器
│   │   ├── crawler/         # 网页爬虫（含 universities 学校适配）
│   │   ├── matcher/         # 匹配算法
│   │   ├── llm/             # LLM 集成
│   │   ├── prompts/         # LLM 提示词与配置
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
conda create -n prof-finder python=3.10
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

### 构建便携发行包

开发者可以在当前平台构建本平台便携包：

```bash
# 在项目根目录下，先激活 conda 环境
conda activate prof-finder

# 安装打包工具（首次）
python -m pip install pyinstaller

# 构建前端、PyInstaller 可执行文件和便携压缩包
python scripts/build_portable.py
```

产物输出到 `dist/portable/`。构建脚本只生成当前操作系统/架构的包；三平台自动构建由 `.github/workflows/portable-release.yml` 在 tag 发布时完成。

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

## 任务队列

后台任务（爬虫、LLM 调用、匹配）使用 **Huey** 管理，后端为 **SQLite**（`SqliteHuey`）。Huey consumer 作为 daemon 线程在 uvicorn 进程内运行 — 无需单独启动 worker 进程或安装 Redis。

- 任务状态同时存储在内存 dict（用于快速 SSE 进度推送）和 `background_tasks` 表中（用于服务器重启后的持久化恢复）。
- 服务器重启时，数据库中状态为 `pending` 或 `running` 的任务会被自动恢复并重新入队。
- Huey 队列的 SQLite 文件默认存储在 `data/huey_tasks.db`（可通过 `HUEY_DB_PATH` 环境变量配置）。
- Worker 线程数默认为 2（可通过 `HUEY_CONSUMER_WORKERS` 调整）。

## License

MIT License


# 继续优化的方向

- 增加对教授个人主页的解析
- 使用 search agent 来广泛搜集教授的信息
- 匹配算法换成更高级的推荐算法，增加 rubrics, reranking 等
- 将 AI 聊天画像优化的前端做成悬浮球，优化更新逻辑，保持聊天的同时让AI自己决定是否需要更新，不需要手动点击按钮
- 学校网站爬虫支持
- 改进各个环节的 prompt