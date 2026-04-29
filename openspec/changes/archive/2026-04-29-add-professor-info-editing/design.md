## Context

教授信息新增后，用户常常需要基于后续阅读到的论文内容或 ArXiv 条目持续修正研究方向、代表论文与备注。现有“更新教授”语义偏向重新爬取 Scholar，无法覆盖“人工主导 + 外部材料辅助”的编辑场景。

同时，PDF 与 ArXiv 输入不应仅绑定教授模块；后续个人信息编辑也需要同类输入能力，因此需要设计为跨实体复用的输入层。

## Goals / Non-Goals

- Goals:
  - 提供教授信息的手动编辑能力（字段可直接修改）
  - 提供 PDF 上传与 ArXiv 链接输入能力，用于辅助更新教授信息
  - 将 PDF/ArXiv 输入抽象为可复用能力，供未来个人信息编辑页面接入
  - 保持“用户确认后落库”的安全更新模式
- Non-Goals:
  - 本次不实现个人信息修改页面
  - 本次不要求引入复杂自动抽取模型（可先用基础提取与人工确认）
  - 本次不改变现有 Scholar 刷新机制语义

## Decisions

- Decision: 引入通用 SourceInput 资源（支持 `pdf` 与 `arxiv`）
  - Why: 避免在教授模块内硬编码上传逻辑，便于后续 profile 编辑复用
- Decision: PDF 解析统一使用 `pymupdf4llm`
  - Why: 输出结构化 Markdown 文本质量较高，适合后续规则提取与人工校对
- Decision: ArXiv 统一使用官方 API 获取元数据与 PDF 链接
  - Why: 来源稳定、字段标准化，便于统一 ID 与版本处理
- Decision: ArXiv 输入强制走“下载 PDF -> 复用 PDF 解析链路”
  - Why: 确保 ArXiv 与手动上传 PDF 在同一解析路径，减少行为分叉
- Decision: 论文总结优先使用 LLM 生成结构化结果（summary + keywords）
  - Why: 相比纯规则截断，LLM 更适合提炼学术问题/方法/结果
- Decision: 论文总结 Prompt 统一放在 `backend/prof_finder/prompts/`
  - Why: 便于版本化管理、复用与后续调参
- Decision: ArXiv 下载的 PDF 作为临时文件处理，解析完成后删除
  - Why: 降低磁盘占用，避免长期堆积中间文件
- Decision: ArXiv PDF 下载失败时保留元数据并允许稍后重试解析
  - Why: 保证用户先可用论文基础信息，不因下载失败丢失整条来源输入
- Decision: 教授编辑采用“两阶段”流程
  1. 收集输入（手动字段、PDF、ArXiv）
  2. 生成待确认更新并由用户提交保存
  - Why: 减少错误覆盖风险，保证用户对最终数据有控制权
- Decision: 来源输入与业务实体弱耦合
  - `SourceInput` 可先独立创建，再在提交编辑时关联到 `Professor`
  - Why: 支持跨页面复用与后续扩展到其他实体

## Risks / Trade-offs

- PDF 文本提取质量不稳定（扫描版、公式较多）
  - Mitigation: 返回提取状态与可预览文本，允许用户完全手动修正
- ArXiv API 可用性与网络抖动
  - Mitigation: 元数据请求与 PDF 下载分步重试，并记录失败原因到 `error_message`
- 临时 PDF 清理失败导致空间泄漏
  - Mitigation: 解析完成后立即删除，并增加定时兜底清理任务
- 复用抽象会增加初期实现复杂度
  - Mitigation: 先定义最小可行字段和接口，避免过度设计

## Migration Plan

1. 增加数据模型：教授补充字段 + SourceInput 模型
2. 增加来源输入 API（PDF 上传、ArXiv 官方 API 拉取、PDF 重试解析）
3. 增加教授编辑 API（预览更新、确认保存）
4. 增加教授编辑页面并接入可复用输入组件
5. 为 SourceInput 提供可被 future profile edit 直接调用的接口契约

## Open Questions

- ArXiv PDF 重试策略上限（重试次数、退避间隔）需要在实现阶段确定默认值
