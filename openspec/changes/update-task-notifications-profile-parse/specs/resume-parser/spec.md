## MODIFIED Requirements
### Requirement: User Confirmation Flow
系统 SHALL 在 CLI 交互式保存前让用户确认解析结果。

#### Scenario: Display parsed result
- **WHEN** CLI 简历解析完成
- **THEN** 以格式化方式显示提取的信息：
  ```
  === 解析结果 ===

  【教育背景】
  - 本科：清华大学 计算机科学 (2018-2022)
  - 硕士：斯坦福大学 人工智能 (2022-2024)

  【科研经历】
  - NLP研究助理 @ ABC实验室
    发表3篇论文，参与机器翻译项目

  【技能】
  Python, TensorFlow, NLP算法

  是否正确？[Y/n/e(编辑)]
  ```

#### Scenario: User confirms
- **WHEN** 用户输入 Y 或回车
- **THEN** 保存解析结果到数据库

#### Scenario: User edits
- **WHEN** 用户输入 e
- **THEN** 进入交互式编辑模式，允许修改各字段

#### Scenario: User rejects
- **WHEN** 用户输入 n
- **THEN** 取消保存，提示可使用 `profile input` 手动输入

## ADDED Requirements
### Requirement: Web Background Profile Parsing
Web 简历上传 SHALL 创建后台任务解析简历，并在解析成功后自动保存到简历列表。

#### Scenario: Start web profile parse task
- **WHEN** Web 用户上传 `.md`、`.markdown`、`.tex` 或 `.latex` 简历并提交标题
- **THEN** API 返回 `{task_id, message}` 而不是解析结果预览
- **AND** 前端将该任务加入任务面板

#### Scenario: Auto-save parsed profile
- **WHEN** `profile-parse` 任务解析成功
- **THEN** 系统创建一条 `UserProfile` 记录
- **AND** SSE 完成事件包含新建简历的 `profile_id` 和标题摘要

#### Scenario: Preserve existing active profile
- **WHEN** 用户已有激活简历且 `profile-parse` 任务保存新简历
- **THEN** 新简历保存为未激活状态
- **AND** 原激活简历保持激活

#### Scenario: Activate first parsed profile
- **WHEN** 用户没有激活简历且 `profile-parse` 任务保存新简历
- **THEN** 新简历保存为激活状态

#### Scenario: No confirmation modal
- **WHEN** Web `profile-parse` 任务解析完成
- **THEN** 前端刷新简历列表
- **AND** 不弹出解析结果确认窗口
