import client from './client'
import type { SourceInput } from '@/types'

export interface SourceInputListResponse {
  items: SourceInput[]
  total: number
  page: number
  page_size: number
  pages: number
}

export const sourceInputsApi = {
  async listByProfessor(professorId: number): Promise<SourceInput[]> {
    const response = await client.get<SourceInputListResponse>('/source-inputs', {
      params: { professor_id: professorId, page_size: 200 },
    })
    return response.data.items
  },

  async createFromArxiv(url: string): Promise<SourceInput> {
    const response = await client.post<SourceInput>('/source-inputs/arxiv', { url })
    return response.data
  },

  async get(id: number): Promise<SourceInput> {
    const response = await client.get<SourceInput>(`/source-inputs/${id}`)
    return response.data
  },
}
