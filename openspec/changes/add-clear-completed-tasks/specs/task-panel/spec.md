## ADDED Requirements

### Requirement: Clear Completed Tasks
前端任务面板 SHALL 在面板头部提供「清空已完成」按钮，允许用户一键批量移除所有已成功完成的任务。

#### Scenario: 存在 completed 任务时按钮可见
- **WHEN** 任务面板中存在至少一个 `completed` 状态的任务
- **THEN** 面板头部显示「清空已完成」按钮

#### Scenario: 无 completed 任务时按钮隐藏
- **WHEN** 任务面板中没有任何 `completed` 状态的任务
- **THEN** 面板头部不显示「清空已完成」按钮

#### Scenario: 点击按钮批量清除
- **WHEN** 用户点击「清空已完成」按钮
- **THEN** 所有 `completed` 状态的任务从面板列表中移除，`pending`/`running`/`failed` 状态的任务不受影响
