## ADDED Requirements

### Requirement: BackgroundTask Table

系统 SHALL 使用 `background_tasks` 表持久化后台任务状态。

#### Scenario: BackgroundTask schema
- **WHEN** 数据库初始化
- **THEN** 创建 `background_tasks` 表，包含以下列：
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `task_id` VARCHAR(36) UNIQUE NOT NULL（UUID）
  - `task_type` VARCHAR(50) NOT NULL
  - `task_name` VARCHAR(200) NOT NULL
  - `user_id` INTEGER NOT NULL REFERENCES users(id)
  - `status` VARCHAR(20) NOT NULL DEFAULT 'pending'
  - `total` INTEGER NOT NULL DEFAULT 0
  - `current` INTEGER NOT NULL DEFAULT 0
  - `success_count` INTEGER NOT NULL DEFAULT 0
  - `failed_count` INTEGER NOT NULL DEFAULT 0
  - `message` TEXT DEFAULT ''
  - `error_message` TEXT DEFAULT ''
  - `results` JSON DEFAULT '[]'
  - `cancel_requested` BOOLEAN DEFAULT FALSE
  - `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
  - `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP

#### Scenario: Task ID uniqueness
- **WHEN** 创建新任务
- **THEN** `task_id` 使用 UUID4 生成，确保全局唯一

#### Scenario: Cascade on user delete
- **WHEN** 用户被删除
- **THEN** 关联的 `background_tasks` 行由外键约束处理（或手动清理）
