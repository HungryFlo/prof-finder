# 设计文档：Vue Web 前端

## Context

Prof-Finder 当前是 CLI 工具，用户通过命令行完成简历上传、教授添加、匹配和邮件生成。虽然功能完整，但：
- 操作繁琐，需要记忆命令
- 数据展示不直观
- 批量操作不便

Web 前端可以显著提升用户体验，同时保留 CLI 作为高级用户的选择。

## Goals / Non-Goals

**Goals**
- 提供完整的 Web 界面覆盖所有 CLI 功能
- 支持多用户注册登录，数据隔离
- 简洁现代的 UI，使用 Naive UI 组件库
- 前后端分离，API 可复用

**Non-Goals**
- 暗色主题（后续迭代）
- 国际化/多语言（后续迭代）
- 第三方登录（GitHub/Google）
- 忘记密码/邮件验证
- 卡片视图（仅表格视图）

## Decisions

### 1. 前端技术栈

**决策**：Vue 3 + TypeScript + Vite + Naive UI + Pinia

**理由**：
- Vue 3 Composition API 更适合 TypeScript
- Vite 开发体验优秀，HMR 快速
- Naive UI 设计现代，TypeScript 支持好
- Pinia 是 Vue 3 官方推荐的状态管理方案

### 2. 认证方案

**决策**：JWT Token（Access Token + Refresh Token）

**理由**：
- 无状态，易于扩展
- 前后端分离架构标准方案
- Access Token 短期有效（30分钟），Refresh Token 长期（7天）

**密码存储**：bcrypt 哈希（通过 passlib）

### 3. 项目结构

**决策**：Monorepo 同级目录结构（方案 A）

```
prof-finder/
├── backend/                 # 后端（原 src/ 迁移至此）
│   ├── prof_finder/
│   │   ├── api/             # 新增：REST API 路由
│   │   ├── cli/             # 保留：CLI 命令
│   │   ├── crawler/
│   │   ├── db/
│   │   ├── llm/
│   │   ├── matcher/
│   │   ├── models/
│   │   ├── parser/
│   │   └── prompts/
│   └── tests/               # 后端测试
├── frontend/                # 前端 Vue 项目
│   ├── src/
│   │   ├── api/             # API 请求封装
│   │   ├── components/      # 通用组件
│   │   ├── composables/     # 组合式函数
│   │   ├── layouts/         # 布局组件
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia stores
│   │   ├── types/           # TypeScript 类型
│   │   ├── utils/           # 工具函数
│   │   └── views/           # 页面组件
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── openspec/                # 规格文档
├── pyproject.toml           # Python 项目配置（需更新路径）
├── README.md
└── .env.example
```

**理由**：
- 结构清晰，前后端职责分明
- 共享同一个 Git 仓库，版本同步
- 方便同时开发调试
- 可独立部署

**迁移影响**：
- 需要将 `src/` 移动到 `backend/`
- 需要将 `tests/` 移动到 `backend/tests/`
- 需要更新 `pyproject.toml` 中的 packages 路径
- CLI 入口点路径需要更新

### 4. API 设计原则

**决策**：RESTful API，资源导向

- 使用标准 HTTP 方法（GET/POST/PUT/DELETE）
- 统一响应格式：`{ "data": ..., "message": "..." }` 或 `{ "error": "...", "detail": "..." }`
- 分页参数：`?page=1&page_size=20`
- 认证：`Authorization: Bearer <token>`

### 5. 管理员账户

**决策**：预置管理员账户，支持环境变量配置

**默认配置**：
- 用户名：`root`（或 `ADMIN_USERNAME` 环境变量）
- 密码：`root123`（或 `ADMIN_PASSWORD` 环境变量）
- 使用默认密码时，首次登录强制修改密码

**管理员能力**：
- 查看所有用户列表
- 重置任意用户密码

### 6. 长时间任务进度通知

**决策**：使用 Server-Sent Events (SSE) 实现实时进度推送

**理由**：
- 进度通知是单向的（服务端 → 客户端），不需要 WebSocket 的双向通信
- 实现比 WebSocket 简单，FastAPI 原生支持
- 浏览器原生支持 `EventSource` API
- 断线自动重连

**涉及的长时间任务**：
- 批量爬取教授信息（3-5秒/人）
- 批量生成邮件（2-5秒/封）

**设计要点**：
- 任务状态保存在内存中，不持久化历史记录
- 支持中途取消，已完成的结果保存到数据库
- 部分失败时继续执行，最终汇总成功/失败数量

**API 设计**：
```
POST /api/tasks/batch-crawl     → { "task_id": "uuid" }
POST /api/tasks/batch-letters   → { "task_id": "uuid" }
GET  /api/tasks/{id}/progress   → SSE stream
POST /api/tasks/{id}/cancel     → { "message": "已取消" }
```

**SSE 事件类型**：
- `progress`: 进度更新
- `complete`: 任务完成
- `cancelled`: 任务取消
- `error`: 致命错误

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| JWT Token 泄露 | Access Token 短期有效；敏感操作要求重新验证 |
| API 暴露后被滥用 | 所有 API 需认证；速率限制（后续） |
| 前后端开发工作量大 | 分阶段实现；优先核心功能 |

## Architecture

### 整体架构

```
┌─────────────────┐      HTTP/REST      ┌─────────────────┐
│                 │  ←───────────────→  │                 │
│   Vue Frontend  │                     │  FastAPI Server │
│   (Naive UI)    │                     │                 │
└─────────────────┘                     └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │     SQLite      │
                                        │    Database     │
                                        └─────────────────┘
```

### 前端页面结构

```
/login              # 登录页
/register           # 注册页
/                   # 首页（重定向到 /profile）
/profile            # 简历管理
/profile/:id        # 简历详情/编辑
/professor          # 教授管理
/professor/:id      # 教授详情
/match              # 匹配结果
/letter             # 邮件管理
/letter/:professorId # 邮件详情/编辑
/settings           # 设置
/admin/users        # 管理员：用户管理
```

### 数据流

```
用户操作 → Vue 组件 → Pinia Store → API 请求 → FastAPI → 数据库
                ↑                                    │
                └────────────── 响应数据 ────────────┘
```

## Open Questions

（无）
