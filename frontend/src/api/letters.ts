import client from './client'
import type { Letter, PaginatedResponse } from '@/types'
import type { TaskStartResponse } from './tasks'

export interface LettersListParams {
  page?: number
  page_size?: number
}

export const lettersApi = {
  async list(params: LettersListParams = {}): Promise<PaginatedResponse<Letter>> {
    const response = await client.get<PaginatedResponse<Letter>>('/letters', {
      params: {
        page: params.page || 1,
        page_size: params.page_size || 20,
      },
    })
    return response.data
  },

  async generate(professorId: number, language: 'zh' | 'en'): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(`/letters/generate/${professorId}`, null, {
      params: { language },
    })
    return response.data
  },

  async get(professorId: number): Promise<Letter> {
    const response = await client.get<Letter>(`/letters/${professorId}`)
    return response.data
  },

  async update(professorId: number, content: string): Promise<Letter> {
    const response = await client.put<Letter>(`/letters/${professorId}`, { content })
    return response.data
  },
}
