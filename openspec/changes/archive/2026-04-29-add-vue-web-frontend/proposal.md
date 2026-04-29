# Change: 添加 Vue Web 前端界面

## Why

当前系统仅支持 CLI 交互，用户体验和操作效率有限。Web 界面可以提供：
- 更直观的数据展示（表格、详情面板）
- 更便捷的批量操作
- 更友好的简历解析结果编辑
- 多用户登录和数据隔离

## What Changes

### 新增功能
- **用户认证系统**：用户名+密码注册/登录，JWT Token 认证，管理员重置密码
- **Vue 3 前端应用**：基于 Naive UI 的 SPA，包含简历管理、教授管理、匹配结果、邮件生成、设置页面
- **REST API 层**：FastAPI 提供完整的 RESTful API 供前端调用
- **用户设置存储**：每个用户独立的 API Key 和偏好配置

### 后端改造
- 新增 `/api/auth/*` 认证端点
- 新增 `/api/profiles/*`、`/api/professors/*`、`/api/match/*`、`/api/letters/*`、`/api/settings/*` REST API
- User 模型增加密码哈希字段和管理员标识
- 新增 UserSettings 模型存储用户配置

### 技术栈
- **前端**：Vue 3 + TypeScript + Vite + Naive UI + Pinia + Vue Router + Axios
- **后端**：FastAPI + JWT (python-jose) + passlib (密码哈希)

## Impact

- Affected specs: 
  - 新增 `web-frontend` - 前端页面和组件规格
  - 新增 `rest-api` - REST API 接口规格
  - 新增 `auth` - 用户认证规格（含管理员初始化、强制改密码）
  - 新增 `user-settings` - 用户设置规格
  - 新增 `async-tasks` - 异步任务进度通知规格（SSE）
- Affected code:
  - 新增 `frontend/` 目录 - Vue 前端项目
  - 新增 `src/prof_finder/api/` - REST API 路由
  - 修改 `src/prof_finder/models/` - 扩展 User 模型
  - 修改 `src/prof_finder/db/` - 新增数据库操作
