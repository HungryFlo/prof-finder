# Change: Add Clear Completed Tasks Button to Task Panel

## Why
任务面板中已完成（completed）的任务会逐渐累积，用户需要逐个点击关闭按钮手动清除，操作繁琐。提供一键清空所有已完成任务的按钮，提升任务面板的使用体验。

## What Changes
- 任务面板头部新增「清空已完成」按钮，仅在存在 `completed` 状态任务时可见
- 点击按钮后，所有 `completed` 状态任务从面板列表中批量移除
- 前端 Pinia store 新增 `clearCompleted` action

## Impact
- Affected specs: task-panel
- Affected code: `frontend/src/components/TaskPanel.vue`, `frontend/src/stores/tasks.ts`
