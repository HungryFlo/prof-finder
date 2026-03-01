# Change: 增加教授信息修改与可复用来源输入能力

## Why

当前系统支持教授信息新增与基础更新，但缺少“新增后可持续手工修订”的完整工作流，尤其缺少以论文 PDF 与 ArXiv 链接作为补充信息来源的能力。这两类输入将成为后续“个人信息修改页面”的基础能力，需要在本次先完成可复用的后端/前端接口与交互模式。

## What Changes

- 新增“教授信息编辑”能力：支持手动编辑字段、上传论文 PDF、提交 ArXiv 链接后辅助更新教授信息
- 新增“来源输入（Source Ingestion）”通用能力：抽象 PDF/ArXiv 输入处理接口与数据结构，供教授编辑与未来个人信息编辑复用
- 明确解析技术路线：PDF 使用 `pymupdf4llm`，ArXiv 使用官方 API，并下载论文 PDF 复用同一 PDF 解析链路
- 明确 ArXiv PDF 生命周期：解析完成后删除临时 PDF；若下载失败则仅保存元数据并支持稍后重试解析
- 新增 LLM 论文总结能力，并将 prompt 统一管理在 `backend/prof_finder/prompts/`
- 补充教授编辑流程中的预览/确认机制，避免外部来源数据直接覆盖人工数据
- 明确本次范围不包含“个人信息修改页面”UI 落地，仅要求复用能力可被该页面直接接入

## Impact

- Affected specs:
  - `data-model`
  - `rest-api`
  - `web-frontend`
- Affected code (expected):
  - `backend/prof_finder/models/`（教授扩展字段与来源输入模型）
  - `backend/prof_finder/api/`（教授编辑与来源输入接口）
  - `frontend/src/views/professor/`（教授编辑页面）
  - `frontend/src/components/`（可复用 PDF/ArXiv 输入组件）
