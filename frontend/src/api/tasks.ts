import client from './client'
import type { TaskListItem } from '@/types'

export interface TaskStartResponse {
  task_id: string
  message: string
  total?: number
}

export interface BatchCrawlRequest {
  scholar_urls: string[]
}

export interface BatchDblpCrawlRequest {
  dblp_urls: string[]
}

export interface BatchLetterRequest {
  professor_ids?: number[]
  top?: number
  language: 'zh' | 'en'
}

export const tasksApi = {
  async startBatchCrawl(urls: string[]): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>('/tasks/batch-crawl', {
      scholar_urls: urls,
    })
    return response.data
  },

  async startBatchDblpCrawl(urls: string[]): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>('/tasks/batch-dblp-crawl', {
      dblp_urls: urls,
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

  async resume(taskId: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(`/tasks/${taskId}/resume`)
    return response.data
  },

  async retry(taskId: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(`/tasks/${taskId}/retry`)
    return response.data
  },

  async listTasks(): Promise<TaskListItem[]> {
    const response = await client.get<TaskListItem[]>('/tasks')
    return response.data
  },

  async createStreamTicket(): Promise<string> {
    const response = await client.post<{ token: string }>('/tasks/stream-ticket')
    return response.data.token
  },

  /**
   * Multiplexed SSE URL for all of the current user's tasks.
   * Uses a short-lived stream ticket instead of the access JWT.
   */
  getStreamUrl(streamToken: string): string {
    return `/api/tasks/stream?token=${encodeURIComponent(streamToken)}`
  },
}
