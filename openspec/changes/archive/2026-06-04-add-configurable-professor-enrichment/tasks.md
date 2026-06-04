## 1. OpenSpec

- [x] 1.1 编写 `proposal.md` / `design.md` 与 spec deltas
- [x] 1.2 运行 `openspec validate add-configurable-professor-enrichment --strict --no-interactive`

## 2. 后端

- [x] 2.1 `UserSettings` 三列 + `database._migrate` ALTER
- [x] 2.2 `enrichment_prefs`（或等价）读取标志与 `planned` 计算；`_enrich_professor_core` / `execute_professor_enrichment` / 批量调用链
- [x] 2.3 `professors` 路由与 `task_manager` 所有入队点；`ProfessorResponse.enrichment_task_total`
- [x] 2.4 CLI `professor` 同步路径

## 3. 前端

- [x] 3.1 设置页开关 + types + i18n
- [x] 3.2 `ProfessorListView` `addTask` 使用 `enrichment_task_total`

## 4. 测试与收尾

- [x] 4.1 `test_api_settings`、教授创建不入队/入队
- [x] 4.2 确认本 `tasks.md` 与实现一致后全部勾选（部署后由维护者执行 `openspec archive`）
