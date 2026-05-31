# Prof-Finder

**Your Ideal Professor Awaits.** 帮助大学生寻找未来 PhD/MPhil 导师的智能匹配系统。

## 项目简介

Prof-Finder 是一款**在本机运行**的研究生导师匹配助手。你的简历、教授名单和匹配结果都保存在自己的电脑上，不会上传到云端服务器。

**适合谁使用：** 正在准备 PhD 或 MPhil 申请、需要整理目标导师名单并撰写套磁信的同学。

**能帮你做什么：** 上传简历建立学术画像 → 添加感兴趣的教授 → 智能匹配推荐 → 生成个性化联络邮件。Web 界面左侧导航与仪表盘上的四步进度一一对应，按顺序完成即可。

## 功能特点

- **智能简历解析**：支持 Markdown 和 LaTeX 格式，优先使用 LLM 进行语义理解，自动回退到正则解析
- **教授信息爬取**：通过 Google Scholar 自动获取教授信息、论文和研究方向
- **智能匹配**：基于研究方向、技能和经历进行智能匹配推荐
- **邮件生成**：使用 DeepSeek API 生成个性化的学术联络邮件
- **多用户支持**：每个用户有独立的简历和教授数据库
- **Web 界面**：Vue 3 + TypeScript + Vite；界面层使用 Naive UI，并配合 Tailwind CSS、shadcn-vue（Reka UI）、vue-i18n 等

## 快速开始

### 方式一：下载便携版（推荐给普通用户）

在 [GitHub Releases](https://github.com/HungryFlo/prof-finder/releases) 下载与你系统匹配的便携包：

- Windows: `Prof-Finder-windows-x64.zip`
- macOS Apple Silicon: `Prof-Finder-macos-arm64.zip`
- Linux: `Prof-Finder-linux-x64.tar.gz`

解压后双击或运行 `Prof-Finder` / `Prof-Finder.exe`。应用会在本机启动服务，并自动打开系统浏览器。

便携版不要求用户安装 Python、Node.js、Poetry 或 npm。解压包内附有 `README-PORTABLE.txt`，含完整使用说明。

默认管理员账号：

- 用户名：`root`
- 密码：`root123`（首次登录需修改）

便携版**首次启动**会在浏览器中引导你选择数据存储目录（数据库、日志、嵌入模型等）；配置保存在解压目录旁的 `install.json`。未完成配置前不会初始化数据库（详见下方 FAQ）。

如需卸载并彻底清理数据，请先关闭正在运行的 Prof-Finder，再运行便携包内的卸载脚本：

- Windows: `uninstall-prof-finder.bat`
- macOS / Linux: `./uninstall-prof-finder.sh`

卸载脚本会要求输入 `DELETE` 确认，然后删除你配置的数据目录、嵌入模型目录，并尽可能删除当前解压出来的便携包目录。该操作不可恢复。

## 普通用户使用指南

完成以下步骤即可从零开始使用：

### 第一步：首次配置、启动并登录

1. 解压便携包到固定目录，运行 `Prof-Finder`（Windows 为 `Prof-Finder.exe`）。
2. 首次启动会自动打开**首次运行配置**页面；选择数据存储目录（模型将保存在其下的 `models` 子目录），完成后应用会自动重启。
3. 重启后使用默认账号 `root` / `root123` 登录。
4. 首次登录会强制要求修改密码，请设置一个安全的新密码。

**macOS 提示：** 若系统提示「无法验证开发者」，请前往「系统设置 → 隐私与安全性」，允许运行该应用。

### 第二步：配置 DeepSeek API Key

1. 登录后点击左侧「设置」。
2. 在「API 配置」卡片中，将 DeepSeek API Key 粘贴到「新 API Key」输入框，点击「保存设置」。

以下功能需要 API Key 才能使用：

- 简历 LLM 智能解析
- 教授科研画像与论文摘要生成
- 套磁邮件生成
- 画像 AI 聊天优化

详见下方「如何获取 DeepSeek API Key」。

### 第三步：建立学生画像

1. 点击左侧「学生画像」→「上传简历」。
2. 选择 `.md`、`.tex`、`.txt` 等格式的简历文件。
3. 建议开启 LLM 自动提取，系统会解析研究方向、技能、教育经历等字段。
4. 上传后可在详情页手动编辑或完善信息。
5. 确保至少有一个画像处于「已激活」状态（匹配时使用激活的画像）。

### 第四步：添加教授

1. 点击左侧「教授」→「添加教授」。
2. 推荐方式（按稳定性排序）：
   - **Google Scholar 链接**：粘贴教授 Scholar 主页 URL，信息最完整。
   - **院校批量爬取**：选择目标院校，后台自动导入教授列表。
   - **手动添加**：填写姓名、单位等基本信息。
3. 添加过程在后台运行，可通过右下角「任务面板」查看进度。

### 第五步：运行匹配

1. 点击左侧「匹配结果」。
2. 首次使用需下载约 400 MB 的嵌入模型（需联网，下载完成后自动启用）。
3. 确认已有激活画像和至少一位教授后，点击「运行匹配」。
4. 匹配完成后，按匹配度排序的教授列表会显示在页面上。

### 第六步：生成套磁邮件

1. 在匹配结果页点击某位教授，打开详情弹窗。
2. 点击「生成邮件」，系统会根据你的画像和教授信息生成个性化套磁信。
3. **务必人工审阅后再发送**，可根据需要编辑内容。

应用内也可点击右上角「使用帮助」查看完整指南。

## 如何获取 DeepSeek API Key

1. 打开 [DeepSeek 开放平台](https://platform.deepseek.com)，注册或登录账号。
2. 进入「API Keys」页面，点击「创建 API Key」。
3. 复制生成的密钥（格式为 `sk-...`）。**密钥只显示一次**，请立即保存。
4. 在 Prof-Finder「设置 → 新 API Key」中粘贴并保存。
5. 在 DeepSeek 平台充值或关注用量；请勿将密钥分享给他人。

## 使用建议

- **先完善画像再匹配**：研究方向、技能、经历越完整，匹配结果越准确。
- **教授来源**：Google Scholar 链接最稳定；院校批量爬取受网站结构影响，可能不完整。
- **匹配前检查**：确保已激活一个画像，且教授列表不为空。
- **套磁信审阅**：AI 生成的邮件仅供参考，发送前请仔细修改。
- **请求延时**：默认 3 秒，用于控制 Scholar 爬取频率；若频繁失败可适当增大。
- **自动增强开关**：「设置」中的教授自动增强（论文摘要、科研画像等）会消耗 API 额度，可按需关闭。

## 常见问题

| 问题 | 解决方法 |
|------|----------|
| 数据存在哪里？ | 首次启动时自选目录；路径记录在程序目录下的 `install.json`。删除解压文件夹不会清除已选数据目录中的内容。 |
| 端口被占用 | 关闭其他 Prof-Finder 实例，或重启电脑后再试。 |
| 浏览器未自动打开 | 手动访问终端/控制台输出的本地地址。 |
| 匹配按钮无法点击 | 先下载嵌入模型；确保有已激活的画像和至少一位教授。 |
| Scholar 爬取失败 | 检查网络连接；在「设置」中增大请求延时；稍后重试。 |
| 如何彻底卸载？ | 关闭应用后运行便携包内的卸载脚本，输入 `DELETE` 确认。仅删除解压文件夹不会清除用户数据。 |
| LLM 功能不可用 | 检查「设置」中是否已配置 DeepSeek API Key，且账户有余额。 |

---

## English User Guide

### About

Prof-Finder is a **locally run** assistant for finding PhD/MPhil supervisors. Your resumes, professor lists, and match results stay on your computer — nothing is uploaded to a cloud server.

**Who it's for:** Students preparing graduate school applications who need to organize target supervisors and draft outreach emails.

**What it does:** Upload your resume to build an academic profile → add professors → get smart match recommendations → generate personalized contact letters. The four steps in the sidebar and dashboard correspond to this workflow.

### Quick Start (Portable Edition)

1. Download the portable package for your OS from [GitHub Releases](https://github.com/HungryFlo/prof-finder/releases).
2. Extract and run `Prof-Finder` (or `Prof-Finder.exe` on Windows).
3. The app starts a local server and opens your browser automatically.
4. Log in with `root` / `root123`, then change your password on first login.
5. Go to **Settings** and enter your DeepSeek API Key.

See `README-PORTABLE.txt` inside the extracted package for the full guide.

### Recommended Workflow

1. **Log in** — Use default credentials, then set a new password.
2. **Configure API Key** — Settings → paste your DeepSeek API Key → Save.
3. **Build a profile** — Student Profiles → Upload resume (`.md`, `.tex`, `.txt`). Enable LLM extraction. Activate one profile for matching.
4. **Add professors** — Professors → Add via Google Scholar URL (recommended), university batch crawl, or manual entry. Track progress in the task panel.
5. **Run matching** — Match Results → download the embedding model on first use (~400 MB, requires internet) → Run Match.
6. **Generate letters** — Open a professor from match results → Generate letter → **Review and edit before sending**.

Click **Help** in the top-right corner of the app for the full in-app guide.

### How to Get a DeepSeek API Key

1. Visit [DeepSeek Platform](https://platform.deepseek.com) and sign up or log in.
2. Go to **API Keys** and create a new key.
3. Copy the key (`sk-...`). **It is shown only once** — save it immediately.
4. Paste it in Prof-Finder under **Settings → New API Key** and save.
5. Top up your DeepSeek account as needed. Do not share your key.

Features that require an API Key: resume LLM parsing, professor research profiles, paper summaries, contact letter generation, and profile AI chat.

### Best Practices

- Complete your profile before running matches — richer data yields better results.
- Google Scholar URLs are the most reliable professor source; university crawls depend on site structure.
- Ensure one profile is active and you have at least one professor before matching.
- Always review AI-generated emails before sending.
- Default request delay is 3 seconds; increase it if Scholar crawling fails frequently.
- Professor auto-enrichment toggles in Settings consume API credits — disable if not needed.

### FAQ

| Question | Answer |
|----------|--------|
| Where is my data stored? | Chosen during first-run setup; path is stored in `install.json` next to the executable. Deleting the extracted folder does **not** remove your chosen data directory. |
| Port already in use | Close other Prof-Finder instances or restart your computer. |
| Browser didn't open | Manually visit the local URL shown in the terminal/console. |
| Match button disabled | Download the embedding model first; ensure an active profile and at least one professor exist. |
| Scholar crawl failed | Check your network; increase request delay in Settings; retry later. |
| How to fully uninstall? | Close the app, run the uninstall script in the package, type `DELETE` to confirm. |
| LLM features not working | Verify your DeepSeek API Key in Settings and check account balance. |

---

## 开发者文档

以下章节面向开发者和高级用户。

### 方式二：开发环境运行

#### 前置要求

- Python 3.10+（与 `pyproject.toml` 中 `>=3.10,<4.0` 一致）
- Node.js **20.19+** 或 **22.12+**（见 `frontend/package.json` 的 `engines`）
- Poetry (Python 包管理)
- Conda (推荐，用于环境管理)

#### 安装

```bash
# 克隆项目
git clone https://github.com/HungryFlo/prof-finder.git
cd prof-finder

# 激活 conda 环境
source activate prof-finder

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

#### 运行

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

### 配置

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

### CLI 使用方法

除了 Web 界面，你也可以使用命令行工具：

#### 1. 添加个人简历

```bash
# 上传 Markdown 简历（默认使用 LLM 智能解析）
prof-finder profile upload resume.md --title "NLP方向申请"

# 上传 LaTeX 简历
prof-finder profile upload cv.tex --title "ML方向申请"

# 禁用 LLM 解析，仅使用正则解析
prof-finder profile upload resume.md --no-llm
```

#### 2. 添加教授

```bash
# 通过 Google Scholar 链接添加
prof-finder professor add --scholar "https://scholar.google.com/citations?user=xxx"

# 搜索教授
prof-finder professor search "Andrew Ng"
```

#### 3. 执行匹配

```bash
prof-finder match run
prof-finder match show --top 10
```

#### 4. 生成联络邮件

```bash
prof-finder letter generate <professor_id>
prof-finder letter batch --top 5
```

### 项目结构

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
│   │   ├── components/     # Vue 组件
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

### 开发

#### 开发环境准备

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

#### 常用命令

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

#### 构建便携发行包

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

#### 本地联调

同时启动后端和前端进行开发：

```bash
# 终端 1：后端
uvicorn backend.prof_finder.api.main:app --reload --port 8000

# 终端 2：前端
cd frontend && npm run dev
```

前端默认代理 `/api` 到 `http://localhost:8000`，无需额外配置。

### API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 任务队列

后台任务（爬虫、LLM 调用、匹配）使用 **Huey** 管理，后端为 **SQLite**（`SqliteHuey`）。Huey consumer 作为 daemon 线程在 uvicorn 进程内运行 — 无需单独启动 worker 进程或安装 Redis。

- 任务状态同时存储在内存 dict（用于快速 SSE 进度推送）和 `background_tasks` 表中（用于服务器重启后的持久化恢复）。
- 服务器重启时，数据库中状态为 `pending` 或 `running` 的任务会被自动恢复并重新入队。
- Huey 队列的 SQLite 文件默认存储在 `data/huey_tasks.db`（可通过 `HUEY_DB_PATH` 环境变量配置）。
- Worker 线程数默认为 2（可通过 `HUEY_CONSUMER_WORKERS` 调整）。

## License

MIT License

## 继续优化的方向

- 增加对教授个人主页的解析
- 使用 search agent 来广泛搜集教授的信息
- 匹配算法换成更高级的推荐算法，增加 rubrics, reranking 等
- 将 AI 聊天画像优化的前端做成悬浮球，优化更新逻辑，保持聊天的同时让AI自己决定是否需要更新，不需要手动点击按钮
- 学校网站爬虫支持
- 改进各个环节的 prompt
