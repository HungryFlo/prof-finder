## MODIFIED Requirements

### Requirement: Frontend Task Panel
前端 SHALL 在 Header 右侧提供任务面板图标，点击展开当前任务进度列表。

#### Scenario: 运行中任务展示
- **WHEN** 有任务处于 `running` 或 `pending` 状态
- **THEN** 图标显示旋转动画，下拉列表中展示任务名和进度（批量任务显示 `X/Y`，单次任务显示"运行中..."）

#### Scenario: 成功任务保留
- **WHEN** 任务状态变为 `completed`
- **THEN** 该任务保留在面板列表中，并显示完成状态

#### Scenario: 失败任务保留
- **WHEN** 任务状态变为 `failed`
- **THEN** 该任务留在面板列表中，显示错误信息和关闭按钮，不影响其他任务的执行和显示

#### Scenario: 手动关闭失败或完成任务
- **WHEN** 用户点击失败或完成任务的关闭按钮
- **THEN** 该任务从面板列表中移除

#### Scenario: 存在 completed 任务时清空按钮可见
- **WHEN** 任务面板中存在至少一个 `completed` 状态的任务
- **THEN** 面板头部显示「清空已完成」按钮

#### Scenario: 无 completed 任务时清空按钮隐藏
- **WHEN** 任务面板中没有任何 `completed` 状态的任务
- **THEN** 面板头部不显示「清空已完成」按钮

#### Scenario: 点击按钮批量清除
- **WHEN** 用户点击「清空已完成」按钮
- **THEN** 所有 `completed` 状态的任务从面板列表中移除，`pending`/`running`/`failed` 状态的任务不受影响

#### Scenario: 面板跨页面持久
- **WHEN** 用户在任务运行期间切换到其他页面
- **THEN** 任务面板仍显示在 Header 中，进度继续更新
