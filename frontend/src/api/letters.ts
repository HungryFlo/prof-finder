import client from './client'
import type { Letter } from '@/types'
import type { TaskStartResponse } from './tasks'

export const lettersApi = {
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
