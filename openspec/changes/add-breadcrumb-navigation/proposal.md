# Change: 添加面包屑导航

## Why
当前没有面包屑导航，尤其在 ProfessorDetailView、ProfileDetailView 等多层嵌套页面，用户容易迷失当前位置。面包屑可以提供清晰的页面层级关系和快速返回上级的路径。

## What Changes
- 在 MainLayout 的主内容区顶部（router-view 上方）添加 `NBreadcrumb` 组件
- 面包屑根据当前路由自动生成：
  - 首页：不显示面包屑（或仅显示「首页」）
  - Profile 列表：首页 > 简历管理
  - Profile 详情：首页 > 简历管理 > {profile title}
  - Professor 列表：首页 > 教授管理
  - Professor 详情：首页 > 教授管理 > {professor name}
  - Match 结果：首页 > 匹配结果
  - 设置：首页 > 设置
  - 管理员用户管理：首页 > 用户管理
- 面包屑项可点击跳转（最后一项不可点击，表示当前页）
- 使用路由 meta 字段配置面包屑标题，详情页标题从页面数据动态获取
- i18n 支持面包屑标签的中英文切换

## Impact
- Affected specs: `web-frontend`
- Affected code: `frontend/src/layouts/MainLayout.vue`, `frontend/src/router/index.ts`（增加 meta 配置）, `frontend/src/locales/zh.json`, `frontend/src/locales/en.json`
