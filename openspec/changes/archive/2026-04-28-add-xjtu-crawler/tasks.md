## 1. OpenSpec

- [x] 1.1 创建 `openspec/changes/add-xjtu-crawler/proposal.md`
- [x] 1.2 创建 `openspec/changes/add-xjtu-crawler/design.md`
- [x] 1.3 创建 `openspec/changes/add-xjtu-crawler/specs/professor-crawler/spec.md`（新能力 ADDED）
- [x] 1.4 运行 `openspec validate add-xjtu-crawler --strict --no-interactive` 通过

## 2. 后端爬虫子包

- [x] 2.1 新建 `backend/prof_finder/crawler/universities/__init__.py`
- [x] 2.2 新建 `backend/prof_finder/crawler/universities/base.py`（`UniversityCrawlerBase` 抽象基类）
- [x] 2.3 新建 `backend/prof_finder/crawler/universities/registry.py`（`REGISTRY` + `get_crawler_info_list()`）
- [x] 2.4 新建 `backend/prof_finder/crawler/universities/xjtu_cs.py`（`XJTUCSCrawler`）

## 3. 后端 API

- [x] 3.1 在 `backend/prof_finder/api/schemas.py` 新增 `UniversityCrawlerInfo`、`UniversityCrawlRequest`
- [x] 3.2 在 `backend/prof_finder/api/task_manager.py` 新增 `execute_university_crawl()` 协程
- [x] 3.3 在 `backend/prof_finder/api/routes/professors.py` 新增 `GET /professors/university-crawlers` 端点
- [x] 3.4 在 `backend/prof_finder/api/routes/professors.py` 新增 `POST /professors/crawl-university` 端点

## 4. 前端

- [x] 4.1 在 `frontend/src/api/professors.ts` 新增 `getUniversityCrawlers()` 和 `crawlUniversity()` 方法
- [x] 4.2 在 `frontend/src/views/professor/ProfessorListView.vue` 新增"院校官网批量添加"按钮及院校选择 Modal

## 5. 测试

- [x] 5.1 新建 `backend/tests/test_xjtu_crawler.py`（mock HTTP 响应，21个测试全部通过）
