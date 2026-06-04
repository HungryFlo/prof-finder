# Change: 可配置的添加/同步后教授自动增强

## Why

添加或从 Scholar 同步教授后自动 enrichment 能提高匹配质量，但三步（爬取论文详情、LLM 论文摘要、科研画像）全跑往往过慢；用户需要按需在设置中关闭部分步骤。

## What Changes

- `UserSettings` 增加三个布尔配置（默认 `true`，与当前「全执行」行为一致），控制自动 enrichment 是否执行：拉取出版物详情、生成英文论文摘要、生成科研画像。
- 后端在手动创建、Scholar 单次/批量/院校导入、Scholar 刷新与批量刷新串联的 `professor-enrichment` / `batch-professor-enrichment` 中读取上述配置；若计划执行子步数为 0 则不创建后台任务。
- `professor-enrichment` 任务的 `total` 为**本次实际会运行的子步数**，每完成一子步递增 `current` 并持久化，供 SSE 与任务列表进度条一致。
- 教授创建/刷新 API 在返回 `enrichment_task_id` 时同时返回 `enrichment_task_total`，供前端任务面板初始进度正确。
- 设置页增加三个开关；CLI `professor add` / `update` 在保存后按同一套 UserSettings 同步执行可执行的子步（计划为 0 则跳过并提示）。

## Impact

- Affected specs: `user-settings`, `rest-api`, `async-tasks`, `web-frontend`, `cli`; `data-model`（UserSettings 列）
- Affected code: `schema.py`, `database.py` `_migrate`, `api/schemas.py`, `routes/settings.py`, `routes/professors.py`, `task_manager.py`, `cli/professor.py`, frontend settings/types/list view/i18n
