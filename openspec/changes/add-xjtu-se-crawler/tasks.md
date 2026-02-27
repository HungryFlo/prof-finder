## 1. OpenSpec

- [ ] 1.1 创建 `openspec/changes/add-xjtu-se-crawler/proposal.md`
- [ ] 1.2 创建 `openspec/changes/add-xjtu-se-crawler/design.md`
- [ ] 1.3 创建 `openspec/changes/add-xjtu-se-crawler/specs/professor-crawler/spec.md`（ADDED 需求）
- [ ] 1.4 运行 `openspec validate add-xjtu-se-crawler --strict --no-interactive` 通过

## 2. 后端爬虫实现

- [ ] 2.1 新建 `backend/prof_finder/crawler/universities/xjtu_se.py`（`XJTUSECrawler`）
  - 解析列表页 `div.teacher > div.teaSub > ul.clearfix > li > a`
  - 对每个详情 URL 访问 `gr.xjtu.edu.cn`，提取邮箱和研究方向
  - 详情页失败时降级为仅列表页信息，继续处理其余教师
- [ ] 2.2 在 `backend/prof_finder/crawler/universities/registry.py` 注册 `"xjtu-se": XJTUSECrawler`

## 3. 测试

- [ ] 3.1 新建 `backend/tests/test_xjtu_se_crawler.py`（mock HTTP 响应，覆盖列表页解析、详情页解析、挑战流程、失败降级）
