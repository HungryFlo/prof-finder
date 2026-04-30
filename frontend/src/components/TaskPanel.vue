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
  NTag,
} from 'naive-ui'
import {
  ListOutline,
  CloseOutline,
  AlertCircleOutline,
  CheckmarkCircleOutline,
} from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import { useTaskStore } from '@/stores/tasks'
import { tasksApi } from '@/api/tasks'
import type { TaskEntry } from '@/stores/tasks'

const taskStore = useTaskStore()
const { t } = useI18n()

const hasAny = computed(() => taskStore.taskList.length > 0)
const runningTasks = computed(() =>
  taskStore.taskList.filter((t) => t.status === 'running' || t.status === 'pending')
)
const failedTasks = computed(() => taskStore.taskList.filter((t) => t.status === 'failed'))
const completedTasks = computed(() => taskStore.taskList.filter((t) => t.status === 'completed'))
const completedCount = computed(() => taskStore.taskList.filter((t) => t.status === 'completed').length)
const badgeValue = computed(() => taskStore.runningCount + taskStore.failedCount || undefined)
const badgeType = computed(() => (taskStore.failedCount > 0 ? 'error' : 'info'))

function progressPercent(task: TaskEntry): number {
  if (task.total === 0) return 0
  return Math.round((task.current / task.total) * 100)
}

function progressLabel(task: TaskEntry): string {
  if (task.status === 'completed') return task.message || t('task.completed')
  if (task.total <= 1) return task.message || ''
  return `${task.current} / ${task.total}`
}

function statusLabel(task: TaskEntry): string {
  if (task.status === 'failed') return t('task.failed')
  if (task.status === 'completed') return t('task.completed')
  if (task.status === 'pending') return ''
  return t('task.running')
}

async function handleCancel(taskId: string) {
  try {
    await tasksApi.cancel(taskId)
  } catch {
    // ignore
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

    <div class="panel-header">
      <n-text style="font-weight: 600; font-size: 14px;">{{ t('task.title') }}</n-text>
      <n-button
        v-if="completedCount > 0"
        text
        size="tiny"
        style="font-size: 12px; color: #999;"
        @click="taskStore.clearCompleted()"
      >
        {{ t('task.clearCompleted') }}
      </n-button>
    </div>

    <n-divider style="margin: 0;" />

    <div v-if="!hasAny" class="panel-empty">
      <n-icon size="28" color="#ccc"><CheckmarkCircleOutline /></n-icon>
      <n-text depth="3" style="font-size: 13px; margin-top: 8px;">{{ t('task.noRunningTasks') }}</n-text>
    </div>

    <div v-else class="panel-list">
      <template
        v-for="section in [
          { key: 'running', title: t('task.running'), tasks: runningTasks },
          { key: 'failed', title: t('task.failed'), tasks: failedTasks },
          { key: 'completed', title: t('task.completed'), tasks: completedTasks },
        ]"
        :key="section.key"
      >
        <div v-if="section.tasks.length > 0" class="task-section">
          <div class="section-title">{{ section.title }}</div>
          <div
            v-for="task in section.tasks"
            :key="task.taskId"
            class="task-item"
            :class="{
              'task-failed': task.status === 'failed',
              'task-completed': task.status === 'completed',
            }"
          >
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

              <n-space align="center" :size="4">
                <n-tag
                  :type="task.status === 'failed' ? 'error' : task.status === 'completed' ? 'success' : 'info'"
                  size="small"
                  round
                >
                  {{ statusLabel(task) }}
                </n-tag>
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
                  {{ t('task.cancel') }}
                </n-button>
              </n-space>
            </n-space>

            <n-progress
              v-if="task.total > 1 && task.status !== 'failed'"
              type="line"
              :percentage="progressPercent(task)"
              :indicator-placement="'inside'"
              :height="16"
              :border-radius="4"
              style="margin-top: 6px;"
            />

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
      </template>
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

.task-section:not(:last-child) {
  border-bottom: 1px solid var(--n-border-color, #f0f0f0);
}

.section-title {
  padding: 8px 14px 4px;
  font-size: 12px;
  font-weight: 600;
  color: #888;
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

.task-completed {
  background-color: #f8fff9;
}

.spinning-icon :deep(.n-button__icon) {
  animation: pulse 1.6s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
</style>
