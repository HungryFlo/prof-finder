# 实现任务清单

## 0. 项目结构迁移

- [x] 0.1 创建 `backend/` 目录
- [x] 0.2 移动 `src/prof_finder/` 到 `backend/prof_finder/`
- [x] 0.3 移动 `tests/` 到 `backend/tests/`
- [x] 0.4 更新 `pyproject.toml`：
  - [x] 修改 packages 路径为 `backend/prof_finder`
  - [x] 更新 CLI 入口点路径
- [x] 0.5 验证 CLI 命令正常工作
- [x] 0.6 验证测试正常运行

## 1. 后端：用户认证系统

- [x] 1.1 扩展 User 模型，添加 `password_hash`、`is_admin`、`must_change_password` 字段
- [x] 1.2 创建 UserSettings 模型（存储 API Key、偏好）
- [x] 1.3 实现密码哈希工具（bcrypt via passlib）
- [x] 1.4 实现 JWT Token 生成和验证（python-jose）
- [x] 1.5 实现管理员账户初始化：
  - [x] 启动时检查并创建 root 账户
  - [x] 支持环境变量配置 `ADMIN_USERNAME`、`ADMIN_PASSWORD`
  - [x] 默认密码时设置 `must_change_password=True`
- [x] 1.6 实现认证 API 路由：
  - [x] POST `/api/auth/register` - 注册（禁止注册 root）
  - [x] POST `/api/auth/login` - 登录（返回 must_change_password 状态）
  - [x] POST `/api/auth/refresh` - 刷新 Token
  - [x] GET `/api/auth/me` - 获取当前用户
  - [x] POST `/api/auth/change-password` - 修改密码
- [x] 1.7 实现认证中间件（依赖注入 `get_current_user`）
- [x] 1.8 实现管理员 API：
  - [x] GET `/api/admin/users` - 用户列表
  - [x] POST `/api/admin/users/{id}/reset-password` - 重置密码

## 2. 后端：REST API

- [x] 2.1 简历 API：
  - [x] GET `/api/profiles` - 列表
  - [x] POST `/api/profiles` - 创建（手动输入）
  - [x] POST `/api/profiles/upload` - 上传文件
  - [x] GET `/api/profiles/{id}` - 详情
  - [x] PUT `/api/profiles/{id}` - 更新
  - [x] DELETE `/api/profiles/{id}` - 删除
  - [x] POST `/api/profiles/{id}/activate` - 激活
  - [x] DELETE `/api/profiles/batch` - 批量删除
- [x] 2.2 教授 API：
  - [x] GET `/api/professors` - 列表（支持分页、筛选）
  - [x] POST `/api/professors` - 手动添加
  - [x] POST `/api/professors/scholar` - Scholar 链接添加
  - [x] POST `/api/professors/search` - 搜索 Scholar
  - [x] GET `/api/professors/{id}` - 详情
  - [x] PUT `/api/professors/{id}` - 更新
  - [x] DELETE `/api/professors/{id}` - 删除
  - [x] POST `/api/professors/{id}/refresh` - 重新爬取
  - [x] DELETE `/api/professors/batch` - 批量删除
- [x] 2.3 匹配 API：
  - [x] POST `/api/match/run` - 运行匹配
  - [x] GET `/api/match/results` - 获取结果
  - [x] GET `/api/match/results/{professor_id}` - 单个详情
- [x] 2.4 邮件 API：
  - [x] POST `/api/letters/generate/{professor_id}` - 生成
  - [x] POST `/api/letters/batch` - 批量生成
  - [x] GET `/api/letters` - 列表
  - [x] GET `/api/letters/{professor_id}` - 详情
  - [x] PUT `/api/letters/{professor_id}` - 更新
- [x] 2.5 设置 API：
  - [x] GET `/api/settings` - 获取
  - [x] PUT `/api/settings` - 更新
- [x] 2.6 异步任务 API（SSE）：
  - [x] 实现任务管理器（内存存储任务状态）
  - [x] POST `/api/tasks/batch-crawl` - 启动批量爬取任务
  - [x] POST `/api/tasks/batch-letters` - 启动批量生成邮件任务
  - [x] GET `/api/tasks/{task_id}/progress` - SSE 进度推送
  - [x] POST `/api/tasks/{task_id}/cancel` - 取消任务
  - [x] 实现部分失败继续执行逻辑
  - [x] 实现取消后保存已完成结果

## 3. 前端：项目搭建

- [x] 3.1 初始化 Vue 3 + TypeScript + Vite 项目
- [x] 3.2 安装配置 Naive UI
- [x] 3.3 配置 Vue Router
- [x] 3.4 配置 Pinia
- [x] 3.5 配置 Axios（请求拦截、响应拦截、Token 注入）
- [x] 3.6 创建项目目录结构
- [x] 3.7 定义 TypeScript 类型

## 4. 前端：认证模块

- [x] 4.1 创建 auth store（用户状态、Token 管理）
- [x] 4.2 实现登录页面
- [x] 4.3 实现注册页面
- [x] 4.4 实现强制修改密码页面（must_change_password）
- [x] 4.5 实现路由守卫（未登录跳转登录页，强制改密码拦截）
- [x] 4.6 实现 Token 自动刷新
- [x] 4.7 实现登出功能

## 5. 前端：布局与导航

- [x] 5.1 创建主布局组件（Header + Sidebar + Content）
- [x] 5.2 实现侧边栏导航菜单
- [x] 5.3 实现用户头像下拉菜单（登出、设置）
- [ ] 5.4 实现面包屑导航（可选，暂未实现）

## 6. 前端：简历管理

- [x] 6.1 创建 profile API 模块
- [x] 6.2 简历列表页（表格 + 批量操作）
- [x] 6.3 上传简历 Modal
- [x] 6.4 手动创建简历 Modal
- [x] 6.5 简历详情/编辑页
- [x] 6.6 解析结果确认与修改

## 7. 前端：教授管理

- [x] 7.1 创建 professor API 模块
- [x] 7.2 教授列表页（表格 + 筛选 + 批量操作）
- [x] 7.3 添加教授 Modal（Scholar 链接 / 手动）
- [ ] 7.4 搜索 Scholar Modal（可选，暂未实现）
- [ ] 7.5 批量添加教授 Modal（多个 Scholar 链接 + 进度显示）（可选，暂未实现）
- [x] 7.6 教授详情 Drawer（基本信息 + 论文列表）

## 8. 前端：匹配功能

- [x] 8.1 创建 match API 模块
- [x] 8.2 匹配结果页（排名列表 + 筛选 + 排序）
- [x] 8.3 运行匹配按钮（带 loading 状态）
- [x] 8.4 匹配详情展示（匹配原因分析）
- [x] 8.5 导出匹配结果（CSV）

## 9. 前端：邮件生成

- [x] 9.1 创建 letter API 模块
- [x] 9.2 邮件列表页
- [x] 9.3 生成邮件按钮
- [ ] 9.4 批量生成 Modal（带进度显示 + 取消功能）（可选，暂未实现）
- [x] 9.5 邮件预览与编辑 Modal
- [x] 9.6 复制到剪贴板功能

## 10. 前端：异步任务通用组件

- [ ] 10.1 创建 task store（管理当前任务状态）（可选，暂未实现）
- [ ] 10.2 实现 SSE 连接封装（useTaskProgress composable）（可选，暂未实现）
- [ ] 10.3 创建任务进度 Modal 组件（可选，暂未实现）
- [ ] 10.4 实现任务取消逻辑（可选，暂未实现）

## 11. 前端：设置页面

- [x] 11.1 账户设置（修改密码）
- [x] 11.2 API 配置（DeepSeek API Key）
- [x] 11.3 管理员页面（用户列表 + 重置密码）

## 12. 集成与测试

- [x] 12.1 前后端联调
- [x] 12.2 编写后端 API 测试
  - [x] 创建测试基础设施（conftest.py with fixtures）
  - [x] 认证 API 测试（注册、登录、刷新、改密码、管理员功能）
  - [x] 简历管理 API 测试（CRUD、上传、激活、批量删除）
  - [x] 教授管理 API 测试（CRUD、分页、筛选、批量删除）
  - [x] 匹配 API 测试（运行匹配、获取结果、详情、分页、筛选）
  - [x] 设置 API 测试（获取、更新、默认值创建）
- [x] 12.3 修复 bug 和完善细节
  - [x] 修复 `KeywordMatcher.match()` 字典/对象类型兼容性问题
  - [x] 修复 `LetterGenerator.__init__()` 缺少 api_key 参数问题
  - [x] 修复 `LetterGenerator._format_professor_info()` 字典访问问题
  - [x] 修复 `SmartParser` 参数名不匹配问题 (`use_llm` → `prefer_llm`)
  - [x] 修复 `SmartParser.parse()` 返回值解构问题
  - [x] 修复 `ScholarCrawler` API 调用问题（方法名和返回值类型）
  - [x] 添加 `extract_scholar_id_from_url()` 辅助函数

## 13. 文档与部署

- [x] 13.1 更新 README（前端启动说明）
- [ ] 13.2 添加开发环境配置说明（可选，后续补充）
- [x] 13.3 更新 .env.example（添加 ADMIN_USERNAME、ADMIN_PASSWORD）

---

## 完成状态说明

核心功能（Phase 0-9, 11, 13）已实现完成，以下功能标记为可选（暂未实现）：
- 面包屑导航
- Scholar 搜索 Modal
- 批量添加教授（进度显示）
- 批量生成邮件（进度显示）
- 前端 SSE 任务进度组件

这些功能的后端 API 已就绪，可在后续迭代中完善前端 UI。
