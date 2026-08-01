import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tasksApi } from '@/api/tasks'
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
}

export interface TaskLifecycleEvent {
  id: number
  taskId: string
  taskType: TaskType
  taskName: string
  status: 'completed' | 'failed' | 'cancelled' | 'interrupted'
  /** User-facing summary shown in notifications. */
  message: string
  /** Raw backend / exception text for the details modal. */
  detail?: string
}

/** Task types that should refresh the professor list when they finish. */
export const PROFESSOR_LIST_REFRESH_TASK_TYPES: TaskType[] = [
  'generic-university-crawl',
  'single-crawl',
  'single-dblp-crawl',
  'batch-dblp-crawl',
  'batch-dblp-match',
  'batch-refresh',
  'batch-refresh-dblp',
  'batch-refresh-external',
  'professor-enrichment',
  'batch-professor-enrichment',
  'batch-professor-profiles',
]

export const useTaskStore = defineStore('tasks', () => {
  const activeTasks = ref<Map<string, TaskEntry>>(new Map())
  const taskEvents = ref<TaskLifecycleEvent[]>([])
  const taskTypeCompleteHandlers = new Map<TaskType, Set<() => void>>()
  const onCompleteHandlers = new Map<string, () => void>()
  let nextEventId = 1
  let sharedEventSource: EventSource | null = null
  let connectingPromise: Promise<void> | null = null

  // ---------------------------------------------------------------------------
  // Computed
  // ---------------------------------------------------------------------------

  const taskList = computed(() => Array.from(activeTasks.value.values()))

  const runningCount = computed(
    () =>
      taskList.value.filter(
        (t) =>
          t.status === 'running' ||
          t.status === 'pending' ||
          t.status === 'cancelling' ||
          t.status === 'interrupted'
      ).length
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
      case 'download-model':
        return t('task.modelDownloadCompleted')
      case 'fill-publications':
        return t('task.abstractsFetched')
      case 'professor-homepage-crawl':
        return t('task.homepageCrawlFinished')
      case 'paper-summary':
        return t('task.paperSummariesFinished')
      case 'single-letter':
      case 'batch-letters':
        return t('task.letterGenerationFinished')
      case 'university-crawl':
      case 'generic-university-crawl':
      case 'batch-crawl':
        return t('task.universityImportFinished', {
          ok: result?.success_count ?? 0,
          fail: result?.failed_count ?? 0,
        })
      case 'batch-dblp-match':
        return t('task.dblpMatchFinished', {
          ok: result?.success_count ?? 0,
          fail: result?.failed_count ?? 0,
        })
      case 'single-crawl':
      case 'single-dblp-crawl':
        return t('task.professorImportFinished')
      case 'batch-refresh':
      case 'batch-refresh-dblp':
      case 'batch-refresh-external':
        return t('task.batchRefreshFinished', {
          ok: result?.success_count ?? 0,
          fail: result?.failed_count ?? 0,
        })
      case 'batch-professor-profiles':
        return t('task.batchProfilesFinished', {
          ok: result?.success_count ?? 0,
          fail: result?.failed_count ?? 0,
        })
      case 'professor-enrichment':
        return t('task.professorEnrichmentFinished')
      case 'batch-professor-enrichment':
        return t('task.batchProfessorEnrichmentFinished', {
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

  function _cancelledMessage(current: number, total: number, message?: string): string {
    if (total > 1) {
      return t('task.cancelledProgress', { current, total })
    }
    return message || t('task.cancelledMessage')
  }

  function _pushTaskEvent(
    entry: TaskEntry,
    status: 'completed' | 'failed' | 'cancelled' | 'interrupted',
    message: string,
    detail?: string,
  ): void {
    taskEvents.value.push({
      id: nextEventId++,
      taskId: entry.taskId,
      taskType: entry.taskType,
      taskName: entry.taskName,
      status,
      message,
      detail,
    })
  }

  function _invokeTaskTypeHandlers(taskType: TaskType): void {
    const handlers = taskTypeCompleteHandlers.get(taskType)
    if (!handlers) return
    for (const handler of handlers) {
      try {
        handler()
      } catch {
        // ignore listener errors
      }
    }
  }

  function registerTaskTypeCompleteHandler(
    taskTypes: TaskType | TaskType[],
    handler: () => void
  ): () => void {
    const types = Array.isArray(taskTypes) ? taskTypes : [taskTypes]
    for (const taskType of types) {
      let set = taskTypeCompleteHandlers.get(taskType)
      if (!set) {
        set = new Set()
        taskTypeCompleteHandlers.set(taskType, set)
      }
      set.add(handler)
    }
    return () => {
      for (const taskType of types) {
        taskTypeCompleteHandlers.get(taskType)?.delete(handler)
      }
    }
  }

  function _taskIdFromEvent(data: { task_id?: string }): string | null {
    return typeof data.task_id === 'string' ? data.task_id : null
  }

  async function _ensureStream(): Promise<void> {
    if (sharedEventSource && sharedEventSource.readyState !== EventSource.CLOSED) {
      return
    }
    if (connectingPromise) {
      return connectingPromise
    }

    connectingPromise = (async () => {
      const streamToken = await tasksApi.createStreamTicket()
      const es = new EventSource(tasksApi.getStreamUrl(streamToken))

      es.addEventListener('progress', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data)
          const taskId = _taskIdFromEvent(data)
          if (!taskId) return
          const entry = activeTasks.value.get(taskId)
          if (!entry) return
          entry.current = data.current ?? entry.current
          entry.total = data.total ?? entry.total
          if (data.cancel_requested) {
            entry.status = 'cancelling'
            entry.message = data.message ?? entry.message
          } else if (entry.status !== 'cancelling') {
            entry.status = data.status ?? entry.status
            entry.message = data.message ?? entry.message
          }
        } catch {
          // malformed event — ignore
        }
      })

      es.addEventListener('complete', (e: MessageEvent) => {
        try {
          const result = JSON.parse(e.data) as TaskResult & { task_id?: string }
          const taskId = _taskIdFromEvent(result)
          if (!taskId) return
          const entry = activeTasks.value.get(taskId)
          if (!entry) return
          if (result.current != null) entry.current = result.current
          if (result.total != null) entry.total = result.total
          entry.status = 'completed'
          entry.message = _completionMessage(entry, result)
          _pushTaskEvent(entry, 'completed', entry.message)
          _invokeTaskTypeHandlers(entry.taskType)
          const cb = onCompleteHandlers.get(taskId)
          onCompleteHandlers.delete(taskId)
          cb?.()
        } catch {
          // ignore
        }
      })

      es.addEventListener('cancelled', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data) as {
            task_id?: string
            current?: number
            total?: number
            message?: string
            completed_count?: number
          }
          const taskId = _taskIdFromEvent(data)
          if (!taskId) return
          const entry = activeTasks.value.get(taskId)
          if (!entry) return
          entry.current = data.current ?? data.completed_count ?? entry.current
          entry.total = data.total ?? entry.total
          entry.status = 'cancelled'
          entry.message = _cancelledMessage(entry.current, entry.total, data.message)
          _pushTaskEvent(entry, 'cancelled', entry.message)
          onCompleteHandlers.delete(taskId)
        } catch {
          // ignore
        }
      })

      es.addEventListener('interrupted', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data) as {
            task_id?: string
            current?: number
            total?: number
            message?: string
          }
          const taskId = _taskIdFromEvent(data)
          if (!taskId) return
          const entry = activeTasks.value.get(taskId)
          if (!entry) return
          entry.current = data.current ?? entry.current
          entry.total = data.total ?? entry.total
          entry.status = 'interrupted'
          entry.message = data.message ?? t('task.interruptedMessage')
          _pushTaskEvent(entry, 'interrupted', entry.message)
          onCompleteHandlers.delete(taskId)
        } catch {
          // ignore
        }
      })

      es.addEventListener('failed', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data) as { task_id?: string; error_message?: string }
          const taskId = _taskIdFromEvent(data)
          if (!taskId) return
          const entry = activeTasks.value.get(taskId)
          if (!entry) return
          entry.status = 'failed'
          entry.errorMessage = data.error_message ?? ''
          _pushTaskEvent(
            entry,
            'failed',
            t('task.taskFailed'),
            entry.errorMessage || undefined,
          )
          onCompleteHandlers.delete(taskId)
        } catch {
          // ignore
        }
      })

      es.onerror = () => {
        // Multiplexed stream dropped — close and reconnect on next ensure.
        es.close()
        if (sharedEventSource === es) {
          sharedEventSource = null
        }
        const hasActive = Array.from(activeTasks.value.values()).some(
          (entry) =>
            entry.status === 'pending' ||
            entry.status === 'running' ||
            entry.status === 'cancelling',
        )
        if (hasActive) {
          void _ensureStream()
        }
      }

      sharedEventSource = es
    })()

    try {
      await connectingPromise
    } finally {
      connectingPromise = null
    }
  }

  // ---------------------------------------------------------------------------
  // Public actions
  // ---------------------------------------------------------------------------

  /**
   * Register a new task and ensure the shared SSE stream is connected.
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
    if (onComplete) {
      onCompleteHandlers.set(taskId, onComplete)
    }
    void _ensureStream()
  }

  function removeTask(taskId: string): void {
    onCompleteHandlers.delete(taskId)
    activeTasks.value.delete(taskId)
  }

  async function requestCancel(taskId: string): Promise<void> {
    const entry = activeTasks.value.get(taskId)
    if (!entry || !['pending', 'running', 'interrupted'].includes(entry.status)) return

    const previousStatus = entry.status
    const previousMessage = entry.message
    if (entry.status === 'interrupted') {
      entry.status = 'cancelling'
      entry.message = t('task.discardingMessage')
    } else {
      entry.status = 'cancelling'
      entry.message = t('task.cancellingMessage')
    }

    try {
      const result = await tasksApi.cancel(taskId)
      entry.current = result.completed_count ?? entry.current
      if (previousStatus === 'interrupted') {
        entry.status = 'cancelled'
        entry.message = t('task.discardedMessage')
        _pushTaskEvent(entry, 'cancelled', entry.message)
      } else {
        entry.message = t('task.cancellingMessage')
      }
    } catch (error) {
      entry.status = previousStatus
      entry.message = previousMessage
      throw error
    }
  }

  async function resumeTask(taskId: string): Promise<void> {
    const entry = activeTasks.value.get(taskId)
    if (!entry || entry.status !== 'interrupted') return

    const previousMessage = entry.message
    entry.status = 'pending'
    entry.message = t('task.resumingMessage')

    try {
      await tasksApi.resume(taskId)
      await _ensureStream()
    } catch (error) {
      entry.status = 'interrupted'
      entry.message = previousMessage
      throw error
    }
  }

  async function retryTask(taskId: string): Promise<void> {
    const entry = activeTasks.value.get(taskId)
    if (!entry || entry.status !== 'failed') return

    activeTasks.value.delete(taskId)
    onCompleteHandlers.delete(taskId)

    const result = await tasksApi.retry(taskId)
    addTask(result.task_id, entry.taskType, entry.taskName, entry.total)
  }

  function clearCompleted(): void {
    for (const [id, entry] of activeTasks.value) {
      if (entry.status === 'completed' || entry.status === 'cancelled') {
        onCompleteHandlers.delete(id)
        activeTasks.value.delete(id)
      }
    }
  }

  function consumeTaskEvents(): TaskLifecycleEvent[] {
    const events = [...taskEvents.value]
    taskEvents.value = []
    return events
  }

  async function discoverChainedTasks(): Promise<void> {
    try {
      const tasks = await tasksApi.listTasks()
      for (const t of tasks) {
        if (activeTasks.value.has(t.task_id)) continue
        if (t.status !== 'running' && t.status !== 'pending') continue
        addTask(t.task_id, t.task_type as TaskType, t.task_name, t.total)
      }
    } catch {
      // Server may be unavailable; fail silently
    }
  }

  async function restoreFromServer(): Promise<void> {
    try {
      const tasks = await tasksApi.listTasks()
      let needsStream = false
      for (const t of tasks) {
        if (activeTasks.value.has(t.task_id)) continue

        const entry = _buildEntry(t.task_id, t.task_type as TaskType, t.task_name, t.total)
        entry.status = t.cancel_requested && (t.status === 'running' || t.status === 'pending')
          ? 'cancelling'
          : (t.status as TaskEntry['status'])
        entry.current = t.current
        entry.message = t.message
        entry.errorMessage = t.error_message
        activeTasks.value.set(t.task_id, entry)

        if (t.status === 'running' || t.status === 'pending') {
          needsStream = true
        }
      }
      if (needsStream) {
        await _ensureStream()
      }
    } catch {
      // Server may be unavailable; fail silently
    }
  }

  function reset(): void {
    sharedEventSource?.close()
    sharedEventSource = null
    connectingPromise = null
    onCompleteHandlers.clear()
    activeTasks.value.clear()
    taskEvents.value = []
    taskTypeCompleteHandlers.clear()
  }

  return {
    activeTasks,
    taskEvents,
    taskList,
    runningCount,
    failedCount,
    addTask,
    removeTask,
    requestCancel,
    resumeTask,
    retryTask,
    clearCompleted,
    consumeTaskEvents,
    discoverChainedTasks,
    registerTaskTypeCompleteHandler,
    restoreFromServer,
    reset,
  }
})
