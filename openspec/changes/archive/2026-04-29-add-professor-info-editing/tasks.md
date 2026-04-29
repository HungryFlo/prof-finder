## 1. OpenSpec

- [x] 1.1 创建 `openspec/changes/add-professor-info-editing/proposal.md`
- [x] 1.2 创建 `openspec/changes/add-professor-info-editing/design.md`
- [x] 1.3 创建以下 spec deltas：
  - `openspec/changes/add-professor-info-editing/specs/data-model/spec.md`
  - `openspec/changes/add-professor-info-editing/specs/rest-api/spec.md`
  - `openspec/changes/add-professor-info-editing/specs/web-frontend/spec.md`
- [x] 1.4 运行 `openspec validate add-professor-info-editing --strict --no-interactive` 并通过

## 2. Backend: 数据模型与来源输入

- [x] 2.1 扩展 Professor 数据结构，支持编辑备注与来源关联
- [x] 2.2 新增 SourceInput 模型，支持 `pdf` 与 `arxiv` 两类来源
- [x] 2.3 实现 PDF 上传处理（文件校验、文本提取、元数据落库）
- [x] 2.4 使用 `pymupdf4llm` 实现 PDF 解析（输出 Markdown 预览）
- [x] 2.5 实现 ArXiv 链接处理（官方 API、ID 规范化、元数据获取）
- [x] 2.6 实现 ArXiv 论文 PDF 下载并复用 PDF 解析链路
- [x] 2.7 实现 ArXiv 临时 PDF 文件清理（解析后删除）
- [x] 2.8 支持 ArXiv 元数据-only 降级与重试 PDF 解析 API
- [x] 2.9 增加教授编辑流程 API（预览更新 + 确认保存）
- [x] 2.10 增加权限校验，确保仅可操作当前用户资源
- [x] 2.11 新增 `paper_summaries` 结构化字段并在来源应用时写入
- [x] 2.12 将 `paper_summaries` 纳入匹配文本构建与匹配计算
- [x] 2.13 使用 LLM 生成论文总结，并将 Prompt 统一放入 `backend/prof_finder/prompts/`

## 3. Frontend: 教授编辑与可复用组件

- [x] 3.1 新增教授编辑页（或现有教授详情中的编辑模式）
- [x] 3.2 支持手动编辑字段并实时校验
- [x] 3.3 集成 PDF 上传入口并展示提取预览
- [x] 3.4 集成 ArXiv 链接入口并展示抓取预览
- [x] 3.5 新建可复用 SourceInput 组件（供未来个人信息编辑复用）
- [x] 3.6 增加“预览变更 + 确认保存”交互，防止直接覆盖
- [x] 3.7 在教授详情新增“论文总结”区块展示

## 4. Tests

- [x] 4.1 后端单元测试：SourceInput 校验、PDF/ArXiv 处理逻辑
- [x] 4.2 后端单元测试：ArXiv 下载 PDF 后与手动 PDF 走同一解析链路
- [x] 4.3 后端单元测试：ArXiv 临时 PDF 解析后删除与清理兜底
- [x] 4.4 后端 API 测试：ArXiv metadata-only 降级与重试解析
- [x] 4.5 后端 API 测试：教授编辑预览/保存、权限与异常分支
- [x] 4.6 后端测试：论文总结生成与返回
- [x] 4.7 后端测试：匹配文本包含论文总结内容
- [x] 4.8 后端单元测试：LLM 总结模块降级逻辑
- [ ] 4.9 前端组件测试：SourceInput 组件输入与错误态
- [ ] 4.10 前端页面测试：教授编辑工作流（手动、PDF、ArXiv）
