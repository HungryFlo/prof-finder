# Change: Add Project Foundation

## Why

Prof-Finder 是一个新项目，需要建立基础架构才能开始功能开发。本提案将创建项目骨架、CLI命令框架、数据模型和简历解析器，为后续的教授匹配和邮件生成功能打下基础。

## What Changes

- 创建项目目录结构和 Poetry 配置
- 实现 Typer CLI 基础框架，包含以下命令：
  - `profile` - 管理个人简历信息（上传/手动输入/查看/编辑）
  - `professor` - 管理教授信息（添加/列表/详情）
  - `match` - 执行匹配算法
  - `letter` - 生成联络邮件
- 定义 SQLite 数据库模型（用户简历、教授信息、匹配记录）
- 实现简历解析器（支持 LaTeX 和 Markdown 格式）
- 配置环境变量管理（.env）

## Impact

- Affected specs: `cli`, `data-model`, `resume-parser` (新建)
- Affected code: 
  - `src/prof_finder/` (新建整个模块)
  - `pyproject.toml` (新建)
  - `.env.example` (新建)
