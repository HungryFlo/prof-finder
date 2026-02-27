# Design: 西安交通大学软件学院教师爬虫

## Context

软件学院官网（`https://se.xjtu.edu.cn/jsdw.htm`）与 CS 学院官网采用相同的 JS 挑战保护机制，但教师列表页面结构不同：教师按职称分组展示为姓名链接列表，详情页指向 `gr.xjtu.edu.cn` 个人主页系统（也使用相同 JS 挑战）。

## Goals / Non-Goals

- Goals:
  - 爬取列表页所有分类（教授/研究员/副教授等）中的教师姓名和详情链接
  - 访问每位教师的 `gr.xjtu.edu.cn` 个人页面，提取邮箱、研究方向等字段
  - 复用现有 JS 挑战解决逻辑（基类提取或模块级函数）
  - 融入现有 `UniversityCrawlerBase` 插件架构，无需修改 API 层
- Non-Goals:
  - 不处理 JS 渲染内容（两站均为静态 HTML 返回，不引入 Playwright）
  - 不自动定期同步
  - 不解析教师发表论文列表

## Decisions

- **列表页解析**：定位 `div.teacher` → `div.teaSub`，从 `h2 > p` 获取分类名称，从 `ul.clearfix > li > a` 获取教师姓名及详情页 URL；无 `href` 的条目仅记录姓名，`source_url` 为列表页 URL。
- **姓名规范化**：将姓名中的全角/半角空格移除（如 `"王 伟"` → `"王伟"`）。
- **详情页解析**：详情链接指向 `gr.xjtu.edu.cn/web/<username>`（Liferay 个人主页）。使用相同 JS 挑战机制获取 cookie，再抓取个人页面；提取邮箱（正则匹配）和研究方向（常见中文关键词段落）。
- **详情页失败处理**：单个详情页失败（包括 502/网络超时/解析异常）时记录 `failed_count` 并继续，仅保留列表页中已获取的 `name`、`affiliation`、`source_url`；整体任务仍标记为 COMPLETED。
- **JS 挑战复用**：将 `_solve_challenge` 和 `_make_session` 提取为模块级函数共享，避免代码重复（在 `xjtu_se.py` 内自包含实现，与 `xjtu_cs.py` 独立，保持简单）。
- **注册**：`REGISTRY["xjtu-se"] = XJTUSECrawler`，前端通过现有 `GET /professors/university-crawlers` 自动发现，无需修改 API 层。

## Risks / Trade-offs

- `gr.xjtu.edu.cn` 的 HTML 结构若与预期不符，详情字段会为空，但任务不会失败 → 回退为仅保存列表页信息
- 内网部署环境中 `gr.xjtu.edu.cn` 若不可达，会产生大量 `failed_count` → 在日志中记录完整错误信息，便于排查

## Migration Plan

无数据库迁移，不修改现有数据模型或 API。

## Open Questions

- 无
