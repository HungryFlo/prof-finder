import client from './client'
import type { Professor, ProfessorListItem, ScholarSearchResult, PaginatedResponse } from '@/types'
import type { TaskStartResponse } from './tasks'

export interface UniversityCrawlerInfo {
  university_id: string
  display_name: string
}

export interface ProfessorCreate {
  name: string
  affiliation?: string
  email?: string
  homepage?: string
  research_interests: string[]
}

export interface ProfessorListParams {
  page?: number
  page_size?: number
  affiliation?: string
  interest?: string
}

export const professorsApi = {
  async list(params: ProfessorListParams = {}): Promise<PaginatedResponse<ProfessorListItem>> {
    const response = await client.get<PaginatedResponse<ProfessorListItem>>('/professors', {
      params: {
        page: params.page || 1,
        page_size: params.page_size || 20,
        affiliation: params.affiliation || undefined,
        interest: params.interest || undefined,
      },
    })
    return response.data
  },

  async create(data: ProfessorCreate): Promise<Professor> {
    const response = await client.post<Professor>('/professors', data)
    return response.data
  },

  async addByScholar(url: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>('/professors/scholar', { url })
    return response.data
  },

  async search(query: string, limit: number = 10): Promise<ScholarSearchResult[]> {
    const response = await client.post<ScholarSearchResult[]>('/professors/search', {
      query,
      limit,
    })
    return response.data
  },

  async get(id: number): Promise<Professor> {
    const response = await client.get<Professor>(`/professors/${id}`)
    return response.data
  },

  async update(id: number, data: Partial<ProfessorCreate>): Promise<Professor> {
    const response = await client.put<Professor>(`/professors/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<{ message: string }> {
    const response = await client.delete<{ message: string }>(`/professors/${id}`)
    return response.data
  },

  async refresh(id: number): Promise<Professor> {
    const response = await client.post<Professor>(`/professors/${id}/refresh`)
    return response.data
  },

  async batchDelete(ids: number[]): Promise<{ message: string }> {
    const response = await client.post<{ message: string }>('/professors/batch-delete', { ids })
    return response.data
  },

  async getUniversityCrawlers(): Promise<UniversityCrawlerInfo[]> {
    const response = await client.get<UniversityCrawlerInfo[]>('/professors/university-crawlers')
    return response.data
  },

  async crawlUniversity(universityId: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>('/professors/crawl-university', {
      university_id: universityId,
    })
    return response.data
  },
}
