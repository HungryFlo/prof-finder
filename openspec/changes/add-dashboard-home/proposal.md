# Change: 新增首页仪表盘

## Why
当前 `/` 直接跳转到 `/profile`，浪费了一个很好的信息聚合机会。用户缺少一个快速了解系统状态和进行常用操作的入口。首页仪表盘可展示关键统计数据、快速操作入口和激励性话语，提升用户体验和使用动力。

## What Changes
- 新增 `/` 路由对应的 `DashboardView.vue` 页面（替换当前的重定向）
- 页面包含：
  - **欢迎区域**：显示当前用户名和一句随机激励话语（中英文随语言切换）
  - **统计卡片**：Profile 数量、Professor 数量、Match 结果数、已生成 Letter 数（4 张卡片，`NStatistic` 组件）
  - **快速操作**：创建 Profile、添加 Professor、运行 Match 的快捷按钮
  - **最近活动**：最近更新的 Profile、最近添加的 Professor 列表（各显示 5 条）
- 侧边栏导航菜单第一项改为「首页」（Dashboard），`/` 不再重定向到 `/profile`
- i18n 增加 Dashboard 相关 key，包括 8-10 条中英文激励话语
- 激励话语每次访问随机展示一条

## Impact
- Affected specs: `web-frontend`, `rest-api`
- Affected code: `frontend/src/views/DashboardView.vue`（新增）, `frontend/src/router/index.ts`, `frontend/src/layouts/MainLayout.vue`, `frontend/src/locales/zh.json`, `frontend/src/locales/en.json`, 可能需要后端新增统计 API
