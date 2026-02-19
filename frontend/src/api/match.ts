import client from './client'
import type { MatchResult, MatchDetail, PaginatedResponse } from '@/types'
import type { TaskStartResponse } from './tasks'

export interface MatchResultsParams {
  page?: number
  page_size?: number
  min_score?: number
}

export const matchApi = {
  async run(): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>('/match/run')
    return response.data
  },

  async getResults(params: MatchResultsParams = {}): Promise<PaginatedResponse<MatchResult>> {
    const response = await client.get<PaginatedResponse<MatchResult>>('/match/results', {
      params: {
        page: params.page || 1,
        page_size: params.page_size || 20,
        min_score: params.min_score || undefined,
      },
    })
    return response.data
  },

  async getDetail(professorId: number): Promise<MatchDetail> {
    const response = await client.get<MatchDetail>(`/match/results/${professorId}`)
    return response.data
  },
}
