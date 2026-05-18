## 1. OpenSpec
- [x] 1.1 Create proposal.md / spec deltas
- [ ] 1.2 Run `openspec validate add-breadcrumb-navigation --strict --no-interactive`

## 2. Frontend - 路由配置
- [x] 2.1 在 router/index.ts 中为每个路由添加 `meta.breadcrumb` 配置（i18n key 或静态文本）
- [x] 2.2 详情页路由使用动态 meta 或在组件中设置面包屑标题

## 3. Frontend - 面包屑组件
- [x] 3.1 在 MainLayout 主内容区顶部添加 `NBreadcrumb`
- [x] 3.2 根据当前路由和 meta 自动生成面包屑路径
- [x] 3.3 详情页面包屑标题从页面数据动态获取（通过 provide/inject 或 route meta 更新）
- [x] 3.4 面包屑项可点击跳转，最后一项（当前页）不可点击

## 4. i18n
- [x] 4.1 新增面包屑标签的中英文 i18n keys（首页、简历管理、教授管理、匹配结果、设置、用户管理）

## 5. Validation
- [ ] 5.1 手动验证：列表页面面包屑显示正确（如 首页 > 教授管理）
- [ ] 5.2 手动验证：详情页面面包屑显示正确（如 首页 > 教授管理 > {name}）
- [ ] 5.3 手动验证：面包屑可点击跳转
- [ ] 5.4 手动验证：语言切换后面包屑标签更新
- [ ] 5.5 Run `openspec validate add-breadcrumb-navigation --strict --no-interactive`
