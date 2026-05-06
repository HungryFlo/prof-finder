## ADDED Requirements

### Requirement: Professor enrichment task progress granularity

系统 SHALL 为 `professor-enrichment` 任务提供与「计划执行的子步」一致的进度计数。

#### Scenario: Total reflects planned sub-steps
- **WHEN** 创建 `professor-enrichment` 任务
- **THEN** `total` 等于针对该教授、按用户设置计算得到的计划子步数（可为 1、2 或 3，或为 0 时不创建任务）

#### Scenario: Current advances per sub-step
- **WHEN** 任务运行中每完成一个已启用且实际执行的子步（出版物详情填充、论文摘要、科研画像）
- **THEN** `current` 递增 1
- **AND** 状态持久化以便 SSE 与任务列表读取一致

#### Scenario: Zero planned sub-steps in worker
- **WHEN** Worker 执行时发现计划子步数为 0
- **THEN** 任务标记为已完成并附带说明性 `message`，不执行 LLM 或爬虫子步
