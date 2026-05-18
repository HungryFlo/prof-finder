## 1. OpenSpec
- [ ] 1.1 Create proposal.md / spec deltas
- [ ] 1.2 Run `openspec validate optimize-settings-layout --strict --no-interactive`

## 2. Frontend - 布局重构
- [x] 2.1 使用 `NGrid` 将 API 配置卡片和 Auto-Enrich 卡片并排（2 列，responsive）
- [x] 2.2 修改密码卡片保持全宽，放在 grid 下方
- [x] 2.3 调整 `label-width` 适配并排布局（可能需要缩短）
- [x] 2.4 窄屏（< 900px）回退为单列堆叠（`NGrid` 的 `responsive` 属性）

## 3. Validation
- [ ] 3.1 手动验证：宽屏下两个卡片并排显示
- [ ] 3.2 手动验证：窄屏下自动回退为单列
- [ ] 3.3 手动验证：所有表单功能不受影响
- [ ] 3.4 Run `openspec validate optimize-settings-layout --strict --no-interactive`
