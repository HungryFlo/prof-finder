## 1. OpenSpec
- [x] 1.1 Create proposal.md / spec deltas
- [x] 1.2 Run `openspec validate add-dashboard-home --strict --no-interactive`

## 2. Backend - 统计 API
- [x] 2.1 ~~新增 `GET /api/dashboard/stats` 接口~~ — 使用现有 list 端点聚合数据，无需新接口
- [x] 2.2 ~~新增 `GET /api/dashboard/recent` 接口~~ — 使用现有 list 端点聚合数据，无需新接口

## 3. Frontend - API 层
- [x] 3.1 新增 `frontend/src/api/dashboard.ts`，封装 stats 和 recent 接口

## 4. Frontend - Dashboard 页面
- [x] 4.1 创建 `frontend/src/views/DashboardView.vue`
- [x] 4.2 欢迎区域：显示用户名 + 随机激励话语
- [x] 4.3 统计卡片：4 张 NStatistic 卡片（Profile、Professor、Match、Letter 数量）
- [x] 4.4 快速操作：3 个 NButton 跳转到创建 Profile、添加 Professor、运行 Match
- [x] 4.5 最近活动：两个 NCard 分别显示最近 Profile 和最近 Professor

## 5. Frontend - 路由与导航
- [x] 5.1 修改 router/index.ts：`/` 不再 redirect 到 `/profile`，改为渲染 DashboardView
- [x] 5.2 修改 MainLayout 侧边栏：第一项改为「首页」（Dashboard icon）
- [x] 5.3 更新 activeKey 计算逻辑以支持 Dashboard 路由

## 6. i18n
- [x] 6.1 新增 Dashboard 相关 i18n keys（页面标题、统计标签、快速操作标签、最近活动标题）
- [x] 6.2 新增 10 条中英文激励话语 i18n keys

## 7. Validation
- [x] 7.1 手动验证：访问 `/` 显示 Dashboard 而非重定向
- [x] 7.2 手动验证：统计数据正确显示
- [x] 7.3 手动验证：快速操作按钮跳转正确
- [x] 7.4 手动验证：激励话语随语言切换
- [x] 7.5 Run `openspec validate add-dashboard-home --strict --no-interactive`
