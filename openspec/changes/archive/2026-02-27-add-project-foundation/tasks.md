# Tasks: Add Project Foundation

## 1. Project Setup

- [x] 1.1 使用 Poetry 初始化项目 (`pyproject.toml`)
- [x] 1.2 创建项目目录结构 (`src/prof_finder/`)
- [x] 1.3 创建 `.env.example` 配置模板
- [x] 1.4 更新 `.gitignore` 添加 Python 相关规则

## 2. Data Model

- [x] 2.1 定义 SQLAlchemy 数据模型 (`models/`)
  - [x] 2.1.1 User 模型（多用户支持）
  - [x] 2.1.2 UserProfile 模型（教育背景、科研经历、技能，支持多简历）
  - [x] 2.1.3 Professor 模型（姓名、院系、研究方向、主页、论文数据，用户隔离）
  - [x] 2.1.4 MatchRecord 模型（匹配结果记录）
- [x] 2.2 实现数据库初始化和迁移逻辑 (`db/`)
- [x] 2.3 编写数据模型单元测试

## 3. Resume Parser

- [x] 3.1 实现 Markdown 简历解析器 (`parser/markdown_parser.py`)
- [x] 3.2 实现 LaTeX 简历解析器 (`parser/latex_parser.py`)
- [x] 3.3 创建解析器统一接口 (`parser/base.py`)
- [x] 3.4 实现解析结果展示与用户确认流程
- [x] 3.5 编写解析器单元测试

## 4. CLI Framework

- [x] 4.1 创建 Typer 应用入口 (`cli/main.py`)
- [x] 4.2 实现 `profile` 命令组
  - [x] 4.2.1 `profile upload` - 上传简历文件
  - [x] 4.2.2 `profile input` - 手动输入信息
  - [x] 4.2.3 `profile show` - 显示当前简历
  - [x] 4.2.4 `profile list` - 列出所有简历
  - [x] 4.2.5 `profile activate` - 激活指定简历
  - [x] 4.2.6 `profile delete` - 删除简历
- [x] 4.3 实现 `professor` 命令组
  - [x] 4.3.1 `professor add` - 添加教授（Google Scholar链接或手动）
  - [x] 4.3.2 `professor list` - 列出已添加的教授
  - [x] 4.3.3 `professor show` - 显示教授详情
  - [x] 4.3.4 `professor update` - 更新教授信息
  - [x] 4.3.5 `professor delete` - 删除教授
  - [x] 4.3.6 `professor search` - 搜索 Google Scholar
- [x] 4.4 实现 `match` 命令
  - [x] 4.4.1 `match run` - 执行匹配算法
  - [x] 4.4.2 `match show` - 显示匹配结果
- [x] 4.5 实现 `letter` 命令
  - [x] 4.5.1 `letter generate` - 生成联络邮件
  - [x] 4.5.2 `letter show` - 显示已生成的邮件
  - [x] 4.5.3 `letter batch` - 批量生成邮件
- [x] 4.6 添加 `--version` 和 `--help` 全局选项

## 5. Configuration

- [x] 5.1 实现配置加载模块 (`config.py`)
- [x] 5.2 支持从 `.env` 读取配置
- [x] 5.3 添加配置验证（必填项检查）

## 6. Additional Modules

- [x] 6.1 实现 Google Scholar 爬虫 (`crawler/scholar.py`)
- [x] 6.2 实现关键词匹配算法 (`matcher/keyword_matcher.py`)
- [x] 6.3 实现 LLM 邮件生成 (`llm/letter_generator.py`)

## 7. Documentation

- [x] 7.1 更新 README.md（安装说明、使用示例）
- [x] 7.2 CLI 自动生成帮助文档（Typer内置）
