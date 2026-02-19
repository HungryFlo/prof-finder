import client from './client'
import type { TaskListItem } from '@/types'

export interface TaskStartResponse {
  task_id: string
  message: string
}

export interface BatchCrawlRequest {
  scholar_urls: string[]
}

export interface BatchLetterRequest {
  professor_ids?: number[]
  top?: number
}

export const tasksApi = {
  async startBatchCrawl(urls: string[]): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>('/tasks/batch-crawl', {
      scholar_urls: urls,
    })
    return response.data
  },

  async startBatchLetters(request: BatchLetterRequest): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>('/tasks/batch-letters', request)
    return response.data
  },

  async cancel(taskId: string): Promise<{ message: string; completed_count: number }> {
    const response = await client.post<{ message: string; completed_count: number }>(
      `/tasks/${taskId}/cancel`
    )
    return response.data
  },

  async listTasks(): Promise<TaskListItem[]> {
    const response = await client.get<TaskListItem[]>('/tasks')
    return response.data
  },

  /**
   * Build an SSE URL for a task, appending the JWT token as a query parameter
   * because the browser's native EventSource API does not support custom headers.
   */
  getProgressUrl(taskId: string, token: string): string {
    return `/api/tasks/${taskId}/progress?token=${encodeURIComponent(token)}`
  },
}
