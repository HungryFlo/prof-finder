# Change: 新增西安交通大学软件学院教师爬虫

## Why

现有爬虫仅覆盖西交大计算机学院，需要进一步支持软件学院（`se.xjtu.edu.cn`）的教师批量导入。软件学院列表页结构与 CS 学院不同（按分类展示姓名链接），详情页托管于独立的 `gr.xjtu.edu.cn` 个人主页系统，需新增专用实现。

## What Changes

- 新增 `backend/prof_finder/crawler/universities/xjtu_se.py`（`XJTUSECrawler`）
- 在 `backend/prof_finder/crawler/universities/registry.py` 中注册 `"xjtu-se"`

## Impact

- Affected specs: professor-crawler
- Affected code:
  - `backend/prof_finder/crawler/universities/xjtu_se.py`（新建）
  - `backend/prof_finder/crawler/universities/registry.py`
  - `backend/tests/test_xjtu_se_crawler.py`（新建）
