import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tasksApi } from '@/api/tasks'
import { useAuthStore } from '@/stores/auth'
import { i18n } from '@/i18n'
import type { TaskType, TaskStatus, TaskResult } from '@/types'

function t(key: string, params?: Record<string, unknown>): string {
  return (i18n.global.t(key, params as any) as string) || key
}

export interface TaskEntry {
  taskId: string
  taskType: TaskType
  taskName: string
  status: TaskStatus
  current: number
  total: number
  message: string
  errorMessage: string
  eventSource?: EventSource
}

export interface TaskLifecycleEvent {
  id: number
  taskId: string
  taskType: TaskType
  taskName: string
  status: 'completed' | 'failed'
  message: string
}

export const useTaskStore = defineStore('tasks', () => {
  const activeTasks = ref<Map<string, TaskEntry>>(new Map())
  const taskEvents = ref<TaskLifecycleEvent[]>([])
  let nextEventId = 1

  // ---------------------------------------------------------------------------
  // Computed
  // ---------------------------------------------------------------------------

  const taskList = computed(() => Array.from(activeTasks.value.values()))

  const runningCount = computed(
    () => taskList.value.filter((t) => t.status === 'running' || t.status === 'pending').length
  )

  const failedCount = computed(() => taskList.value.filter((t) => t.status === 'failed').length)

  // ---------------------------------------------------------------------------
  // Internal helpers
  // ---------------------------------------------------------------------------

  function _buildEntry(
    taskId: string,
    taskType: TaskType,
    taskName: string,
    total: number
  ): TaskEntry {
    return {
      taskId,
      taskType,
      taskName,
      status: 'pending',
      current: 0,
      total,
      message: '',
      errorMessage: '',
    }
  }

  function _completionMessage(entry: TaskEntry, result?: TaskResult): string {
    switch (entry.taskType) {
      case 'profile-parse':
      case 'profile-generate': {
        const profile = result?.results.find((item) => item.success && typeof item.title === 'string')
        return profile?.title
          ? t('task.profileGenerated', { title: profile.title })
          : t('task.profileGenerated', { title: '' })
      }
      case 'profile-refine':
        return t('task.profileRefinementComplete')
      case 'professor-profile': {
        const professor = result?.results.find((item) => item.success && typeof item.name === 'string')
        return professor?.name
          ? t('task.professorProfileGenerated', { name: professor.name })
          : t('task.professorProfileGenerated', { name: '' })
      }
      case 'match':
        return t('task.matchCompleted')
      case 'fill-publications':
        return t('task.abstractsFetched')
      case 'paper-summary':
        return t('task.paperSummariesFinished')
      case 'single-letter':
      case 'batch-letters':
        return t('task.letterGenerationFinished')
      case 'university-crawl':
      case 'batch-crawl':
        return t('task.universityImportFinished', {
          ok: result?.success_count ?? 0,
          fail: result?.failed_count ?? 0,
        })
      case 'single-crawl':
        return t('task.professorImportFinished')
      case 'batch-refresh':
        return t('task.batchRefreshFinished', {
          ok: result?.success_count ?? 0,
          fail: result?.failed_count ?? 0,
        })
      case 'batch-professor-profiles':
        return t('task.batchProfilesFinished', {
          ok: result?.success_count ?? 0,
          fail: result?.failed_count ?? 0,
        })
      default:
        break
    }

    if (result?.message && result.message !== entry.message) {
      return result.message
    }
    return entry.message || t('task.taskCompleted')
  }

  function _pushTaskEvent(
    entry: TaskEntry,
    status: 'completed' | 'failed',
    message: string
  ): void {
    taskEvents.value.push({
      id: nextEventId++,
      taskId: entry.taskId,
      taskType: entry.taskType,
      taskName: entry.taskName,
      status,
      message,
    })
  }

  function _connectSSE(taskId: string, onComplete?: () => void): void {
    const authStore = useAuthStore()
    const token = authStore.accessToken ?? ''
    const url = tasksApi.getProgressUrl(taskId, token)

    const es = new EventSource(url)

    es.addEventListener('progress', (e: MessageEvent) => {
      const entry = activeTasks.value.get(taskId)
      if (!entry) return
      try {
        const data = JSON.parse(e.data)
        entry.current = data.current ?? entry.current
        entry.total = data.total ?? entry.total
        entry.status = data.status ?? entry.status
        entry.message = data.message ?? entry.message
      } catch {
        // malformed event — ignore
      }
    })

    es.addEventListener('complete', (e: MessageEvent) => {
      const entry = activeTasks.value.get(taskId)
      if (entry) {
        let result: TaskResult | undefined
        try {
          result = JSON.parse(e.data)
        } catch {
          result = undefined
        }
        // Fill progress bar so it never shows empty after completion
        if (result?.current != null) entry.current = result.current
        if (result?.total != null) entry.total = result.total
        entry.status = 'completed'
        entry.message = _completionMessage(entry, result)
        _pushTaskEvent(entry, 'completed', entry.message)
      }
      es.close()
      onComplete?.()
    })

    es.addEventListener('cancelled', () => {
      es.close()
      activeTasks.value.delete(taskId)
    })

    es.addEventListener('failed', (e: MessageEvent) => {
      const entry = activeTasks.value.get(taskId)
      if (!entry) return
      entry.status = 'failed'
      try {
        const data = JSON.parse(e.data)
        entry.errorMessage = data.error_message ?? t('task.taskFailed')
      } catch {
        entry.errorMessage = t('task.taskFailed')
      }
      _pushTaskEvent(entry, 'failed', entry.errorMessage)
      es.close()
    })

    es.onerror = () => {
      const entry = activeTasks.value.get(taskId)
      if (entry && entry.status !== 'completed' && entry.status !== 'failed') {
        entry.status = 'failed'
        entry.errorMessage = t('task.taskFailed')
        _pushTaskEvent(entry, 'failed', entry.errorMessage)
      }
      es.close()
    }

    // Store EventSource reference so it can be closed on manual removal
    const entry = activeTasks.value.get(taskId)
    if (entry) entry.eventSource = es
  }

  // ---------------------------------------------------------------------------
  // Public actions
  // ---------------------------------------------------------------------------

  /**
   * Register a new task and open an SSE connection to track its progress.
   *
   * @param taskId   - ID returned by the API when the task was started.
   * @param taskType - Task type string from the API.
   * @param taskName - Human-readable task name.
   * @param total    - Total items to process (used for progress bar).
   * @param onComplete - Optional callback invoked once the task succeeds.
   */
  function addTask(
    taskId: string,
    taskType: TaskType,
    taskName: string,
    total: number,
    onComplete?: () => void
  ): void {
    const entry = _buildEntry(taskId, taskType, taskName, total)
    activeTasks.value.set(taskId, entry)
    _connectSSE(taskId, onComplete)
  }

  /**
   * Manually remove a task (e.g. after dismissing a failed task).
   * Also closes the associated EventSource if still open.
   */
  function removeTask(taskId: string): void {
    const entry = activeTasks.value.get(taskId)
    if (entry?.eventSource) {
      entry.eventSource.close()
    }
    activeTasks.value.delete(taskId)
  }

  /**
   * Remove all tasks that have reached the `completed` status.
   */
  function clearCompleted(): void {
    for (const [id, entry] of activeTasks.value) {
      if (entry.status === 'completed') {
        entry.eventSource?.close()
        activeTasks.value.delete(id)
      }
    }
  }

  function consumeTaskEvents(): TaskLifecycleEvent[] {
    const events = [...taskEvents.value]
    taskEvents.value = []
    return events
  }

  /**
   * Call GET /api/tasks on startup to recover tasks that are still running
   * on the backend after a page refresh.
   */
  async function restoreFromServer(): Promise<void> {
    try {
      const tasks = await tasksApi.listTasks()
      for (const t of tasks) {
        if (!activeTasks.value.has(t.task_id)) {
          const entry = _buildEntry(t.task_id, t.task_type, t.task_name, t.total)
          entry.status = t.status
          entry.current = t.current
          entry.message = t.message
          entry.errorMessage = t.error_message
          activeTasks.value.set(t.task_id, entry)

          // For running/pending tasks, reconnect SSE; failed tasks need no SSE
          if (t.status === 'running' || t.status === 'pending') {
            _connectSSE(t.task_id)
          }
        }
      }
    } catch {
      // Server may be unavailable; fail silently
    }
  }

  return {
    activeTasks,
    taskEvents,
    taskList,
    runningCount,
    failedCount,
    addTask,
    removeTask,
    clearCompleted,
    consumeTaskEvents,
    restoreFromServer,
  }
})
