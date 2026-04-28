# Design: 院校官网批量导入教授

## Context

每所院校官网结构不同，需要可扩展的插件化设计。当前已有 Google Scholar 爬虫和成熟的后台任务/SSE 体系，新功能需融入现有架构。

## Goals / Non-Goals

- Goals:
  - 支持按院校批量爬取教授列表（列表页 + 详情页两步抓取）
  - 可扩展注册表，后续添加新院校只需新增一个文件
  - 复用现有后台任务 + SSE 进度推送机制
  - 前端动态读取已注册院校列表，无硬编码
- Non-Goals:
  - 不支持 JS 渲染页面（不引入 Playwright，XJTU 官网为静态 HTML）
  - 不实现自动定期更新（手动触发即可）

## Decisions

- **子包结构**：`crawler/universities/` 下包含 `base.py`（抽象基类）、`registry.py`（注册表）、各院校实现文件（如 `xjtu_cs.py`）。注册时在 `registry.py` 的 `REGISTRY` 字典中手动添加，不使用自动发现（保持简单可追踪）。
- **抽象基类字段**：`university_id: str`（唯一标识，如 `"xjtu-cs"`）、`display_name: str`（前端展示名，如 `"西安交通大学 - 计算机科学与技术学院"`）、`crawl_all(delay: float) -> list[dict]` 方法。
- **工具选型**：`requests` + `BeautifulSoup4`，两者已在 `pyproject.toml` 中声明；不引入新依赖。
- **去重策略**：按 `(user_id, name, affiliation)` 检查是否已存在，已存在则跳过（不更新），与 Google Scholar 批量爬取行为一致。
- **任务类型**：新增 `task_type = "university-crawl"`，`task_name` 使用爬虫的 `display_name`。

## Risks / Trade-offs

- XJTU 官网 HTML 结构若发生变化，CSS 选择器会失效 → 爬虫代码集中在单文件中，修复成本低
- 爬取过程受网络影响，详情页可能超时 → 单个详情页失败时记录 failed_count 并继续，不中断整批任务

## Migration Plan

无数据库迁移，不修改现有数据模型。

## Open Questions

- 无
