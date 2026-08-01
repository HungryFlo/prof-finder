# Prof-Finder 开发者文档

[← 返回 README](../README.md)

## 开发环境运行

### 前置要求

- Python 3.11+（与 `pyproject.toml` 中 `>=3.11,<4.0` 一致）
- Node.js **20.19+** 或 **22.12+**（见 `frontend/package.json` 的 `engines`）
- Poetry (Python 包管理)
- Conda (推荐，用于环境管理)

### 安装

```bash
git clone https://github.com/HungryFlo/prof-finder.git
cd prof-finder

conda activate prof-finder

poetry install

cd frontend && npm install && cd ..

cp .env.example .env
# 编辑 .env，填入 LLM API 等配置
```

### 运行

**后端**

```bash
uvicorn backend.prof_finder.api.main:app --reload --port 8000
```

**前端**（另开终端）

```bash
cd frontend && npm run dev
```

访问 http://localhost:5173 。前端默认将 `/api` 代理到 `http://localhost:8000`。

默认管理员：`root` / `root123`（首次登录须修改）。可通过 `ADMIN_USERNAME`、`ADMIN_PASSWORD` 环境变量覆盖。

## 配置

编辑 `.env`：

```bash
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
DATABASE_PATH=./data/prof_finder.db
REQUEST_DELAY=3
ADMIN_USERNAME=root
ADMIN_PASSWORD=root123
JWT_SECRET_KEY=your_stable_secret_here
```

完整示例见仓库根目录 [`.env.example`](../.env.example)。

### 部署与安全

- **默认仅本机使用**；若绑定 `0.0.0.0`，请立即修改默认密码并限制访问范围。
- **开放注册**：Web 端允许注册，勿在不可信网络长期暴露实例。
- **API Key**：保存在本地 SQLite；勿提交 `.env` 或数据库目录。

### 合规与免责声明

- 爬取 Google Scholar、院校网站、DBLP 等须遵守各平台 ToS、版权与 robots 规则，合理设置 `REQUEST_DELAY`。
- AI 生成内容仅供参考，发送前须人工审阅。

## CLI

```bash
# 上传简历
prof-finder profile upload resume.md --title "NLP方向申请"
prof-finder profile upload cv.tex --no-llm

# 添加教授
prof-finder professor add --scholar "https://scholar.google.com/citations?user=xxx"
prof-finder professor search "Andrew Ng"

# 匹配（CLI 当前为关键词匹配；Web「运行匹配」使用 Qwen3 语义嵌入）
prof-finder match run
prof-finder match show --top 10

# 邮件
prof-finder letter generate <professor_id>
prof-finder letter batch --top 5
```

> **说明**：日常申请流程以 Web UI / API 为准。CLI 便于脚本化调试，部分能力（尤其匹配算法）与 Web 路径不完全等同。

## 项目结构

```
prof-finder/
├── backend/prof_finder/   # API、CLI、爬虫、匹配、LLM 等
├── backend/tests/
├── frontend/src/
├── packaging/             # PyInstaller 规格等
├── scripts/               # 构建、ModelScope 检测、第三方声明生成等
└── docs/                  # 用户与开发文档
```

## 常用命令

```bash
python -m pytest backend/tests/ -v
black backend/
mypy backend/
cd frontend && npm run build
```

## 构建便携包

```bash
conda activate prof-finder
python -m pip install pyinstaller
python scripts/build_portable.py
```

产物在 `dist/portable/`。Windows 与 macOS 的 Release 由 [`.github/workflows/portable-release.yml`](../.github/workflows/portable-release.yml) 在 tag 时构建。

## API 文档

后端启动后：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 任务队列

后台任务使用 **Huey**（`SqliteHuey`），consumer 在 uvicorn 进程内以 daemon 线程运行，无需 Redis。

- 进度：内存 dict + SSE；持久化：`background_tasks` 表
- 启动恢复（`_rehydrate_tasks`）：
  - 仍为 `pending` 的任务重新入队；
  - 崩溃时处于 `running` 的任务标为 `interrupted`，由用户在任务面板选择「继续」或「放弃」（避免静默从头重跑导致重复写入）。
- 队列库默认 `data/huey_tasks.db`（`HUEY_DB_PATH`）
- Worker 数默认 2（`HUEY_CONSUMER_WORKERS`）

设计细节见 [前端与后台任务](./frontend-and-tasks.zh.md)。

## 许可证与第三方声明

- 本项目代码：[MIT License](../LICENSE)
- 第三方组件清单：[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)（Python 生产依赖、前端 npm 生产依赖、嵌入模型与外部服务）
- 更新依赖后请执行：`python scripts/generate_third_party_notices.py`（需 `poetry install --with dev` 与 `frontend/node_modules`）
- 便携包构建会自动复制 `LICENSE` 与 `THIRD_PARTY_NOTICES.md` 到发行目录

## 文档与规格

- 用户流程：[用户使用指南](./user-guide.zh.md)
- 架构与任务系统：[前端与后台任务](./frontend-and-tasks.zh.md)
- 行为以仓库代码与上述文档为准（仓库中当前无独立 `openspec/` 目录）。
