<script setup lang="ts">
import { computed } from 'vue'
import {
  NButton,
  NIcon,
  NBadge,
  NPopover,
  NSpace,
  NText,
  NProgress,
  NSpin,
  NDivider,
} from 'naive-ui'
import {
  ListOutline,
  CloseOutline,
  AlertCircleOutline,
  CheckmarkCircleOutline,
} from '@vicons/ionicons5'
import { useTaskStore } from '@/stores/tasks'
import { tasksApi } from '@/api/tasks'
import type { TaskEntry } from '@/stores/tasks'

const taskStore = useTaskStore()

const hasAny = computed(() => taskStore.taskList.length > 0)
const completedCount = computed(() => taskStore.taskList.filter((t) => t.status === 'completed').length)
const badgeValue = computed(
  () =>
    taskStore.runningCount +
      taskStore.failedCount +
      completedCount.value || undefined
)
const badgeType = computed(() => (taskStore.failedCount > 0 ? 'error' : 'info'))

function progressPercent(task: TaskEntry): number {
  if (task.total === 0) return 0
  return Math.round((task.current / task.total) * 100)
}

function progressLabel(task: TaskEntry): string {
  if (task.total <= 1) return task.message || '运行中...'
  return `${task.current} / ${task.total}`
}

async function handleCancel(taskId: string) {
  try {
    await tasksApi.cancel(taskId)
  } catch {
    // ignore — task may have already finished
  }
}

function handleDismiss(taskId: string) {
  taskStore.removeTask(taskId)
}
</script>

<template>
  <n-popover
    placement="bottom-end"
    trigger="click"
    :show-arrow="false"
    content-style="padding: 0; min-width: 300px; max-width: 360px;"
  >
    <template #trigger>
      <n-badge :value="badgeValue" :type="badgeType" :max="9">
        <n-button quaternary circle size="medium" :class="{ 'spinning-icon': taskStore.runningCount > 0 }">
          <template #icon>
            <n-icon size="18"><ListOutline /></n-icon>
          </template>
        </n-button>
      </n-badge>
    </template>

    <!-- Panel header -->
    <div class="panel-header">
      <n-text style="font-weight: 600; font-size: 14px;">任务进度</n-text>
      <n-button
        v-if="completedCount > 0"
        text
        size="tiny"
        style="font-size: 12px; color: #999;"
        @click="taskStore.clearCompleted()"
      >
        清空已完成
      </n-button>
    </div>

    <n-divider style="margin: 0;" />

    <!-- Empty state -->
    <div v-if="!hasAny" class="panel-empty">
      <n-icon size="28" color="#ccc"><CheckmarkCircleOutline /></n-icon>
      <n-text depth="3" style="font-size: 13px; margin-top: 8px;">暂无运行中的任务</n-text>
    </div>

    <!-- Task list -->
    <div v-else class="panel-list">
      <div
        v-for="task in taskStore.taskList"
        :key="task.taskId"
        class="task-item"
        :class="{ 'task-failed': task.status === 'failed' }"
      >
        <!-- Task name row -->
        <n-space justify="space-between" align="center" style="width: 100%;">
          <n-space align="center" :size="6">
            <n-spin v-if="task.status === 'running' || task.status === 'pending'" :size="14" />
            <n-icon v-else-if="task.status === 'failed'" color="#e03131" size="16">
              <AlertCircleOutline />
            </n-icon>
            <n-icon v-else-if="task.status === 'completed'" color="#2f9e44" size="16">
              <CheckmarkCircleOutline />
            </n-icon>
            <n-text style="font-size: 13px; font-weight: 500;">{{ task.taskName }}</n-text>
          </n-space>

          <!-- Cancel (running) or dismiss (failed) -->
          <n-button
            v-if="task.status === 'failed' || task.status === 'completed'"
            quaternary
            circle
            size="tiny"
            @click="handleDismiss(task.taskId)"
          >
            <template #icon><n-icon size="14"><CloseOutline /></n-icon></template>
          </n-button>
          <n-button
            v-else-if="task.status === 'running'"
            quaternary
            size="tiny"
            style="font-size: 11px; color: #999;"
            @click="handleCancel(task.taskId)"
          >
            取消
          </n-button>
        </n-space>

        <!-- Progress bar (batch tasks) -->
        <n-progress
          v-if="task.total > 1 && task.status !== 'failed'"
          type="line"
          :percentage="progressPercent(task)"
          :indicator-placement="'inside'"
          :height="16"
          :border-radius="4"
          style="margin-top: 6px;"
        />

        <!-- Status text -->
        <n-text
          v-if="task.status === 'failed'"
          depth="3"
          style="font-size: 12px; color: #e03131; display: block; margin-top: 4px; word-break: break-all;"
        >
          {{ task.errorMessage.length > 80 ? task.errorMessage.slice(0, 80) + '…' : task.errorMessage }}
        </n-text>
        <n-text
          v-else
          depth="3"
          style="font-size: 12px; display: block; margin-top: 4px;"
        >
          {{ progressLabel(task) }}
        </n-text>
      </div>
    </div>
  </n-popover>
</template>

<style scoped>
.panel-header {
  padding: 10px 14px 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 0;
}

.panel-list {
  max-height: 400px;
  overflow-y: auto;
}

.task-item {
  padding: 10px 14px;
  border-bottom: 1px solid var(--n-border-color, #f0f0f0);
}

.task-item:last-child {
  border-bottom: none;
}

.task-failed {
  background-color: #fff5f5;
}

/* Subtle pulse on the icon button when tasks are running */
.spinning-icon :deep(.n-button__icon) {
  animation: pulse 1.6s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
</style>
