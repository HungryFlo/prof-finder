# Change: 新增院校官网批量导入教授功能

## Why

现有教授添加方式依赖逐个提供 Google Scholar 链接，无法批量获取某高校全系教授信息。各院校官网通常有结构化的教师列表页，可按院系一键导入全部教授数据，大幅提升使用效率。

## What Changes

- 新增 `crawler/universities/` 爬虫子包，包含抽象基类、注册表和首批西交大 CS 实现
- 新增通用后台任务协程 `execute_university_crawl()`，走现有 SSE 长任务流程
- 新增 API 端点：`GET /professors/university-crawlers`（查询已注册院校列表）和 `POST /professors/crawl-university`（触发爬取）
- 新增 Pydantic schema：`UniversityCrawlerInfo`、`UniversityCrawlRequest`
- 前端教授列表页新增"院校官网批量添加"按钮，点击弹出院校选择弹窗

## Impact

- Affected specs: professor-crawler（新建）
- Affected code:
  - `backend/prof_finder/crawler/universities/`（新建子包）
  - `backend/prof_finder/api/task_manager.py`
  - `backend/prof_finder/api/routes/professors.py`
  - `backend/prof_finder/api/schemas.py`
  - `frontend/src/api/professors.ts`
  - `frontend/src/views/professor/ProfessorListView.vue`
