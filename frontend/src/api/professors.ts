import client from './client'
import type {
  Professor,
  PaperSummary,
  ProfessorListItem,
  ScholarSearchResult,
  PaginatedResponse,
  ProfessorEditPreviewResponse,
} from '@/types'
import type { TaskStartResponse } from './tasks'

/** Same-origin connection limit + one EventSource per running task (e.g. 教授信息增强) can queue short POSTs. */
const POST_BEHIND_SSE_TIMEOUT_MS = 120_000

export interface UniversityCrawlerInfo {
  university_id: string
  display_name: string
}

export interface ProfessorCreate {
  name: string
  name_locales?: Record<string, string>
  affiliation?: string
  email?: string
  homepage?: string
  research_interests: string[]
  manual_notes?: string
  paper_summaries?: PaperSummary[]
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
    const response = await client.post<Professor>('/professors', data, {
      timeout: POST_BEHIND_SSE_TIMEOUT_MS,
    })
    return response.data
  },

  async addByScholar(url: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      '/professors/scholar',
      { url },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
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

  async editPreview(
    id: number,
    payload: {
      manual_patch?: Partial<ProfessorCreate>
      source_input_ids?: number[]
    }
  ): Promise<ProfessorEditPreviewResponse> {
    const response = await client.post<ProfessorEditPreviewResponse>(
      `/professors/${id}/edit-preview`,
      payload
    )
    return response.data
  },

  async applyEdits(
    id: number,
    payload: {
      manual_patch?: Partial<ProfessorCreate>
      source_input_ids?: number[]
    }
  ): Promise<Professor> {
    const response = await client.post<Professor>(`/professors/${id}/apply-edits`, payload)
    return response.data
  },

  async startPaperSummary(id: number, sourceInputIds: number[]): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(`/professors/${id}/summarize-sources`, {
      source_input_ids: sourceInputIds,
    })
    return response.data
  },

  async delete(id: number): Promise<{ message: string }> {
    const response = await client.delete<{ message: string }>(`/professors/${id}`)
    return response.data
  },

  async refresh(id: number): Promise<Professor> {
    const response = await client.post<Professor>(`/professors/${id}/refresh`, {}, {
      timeout: POST_BEHIND_SSE_TIMEOUT_MS,
    })
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
    const response = await client.post<TaskStartResponse>(
      '/professors/crawl-university',
      { university_id: universityId },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async generateProfile(id: number): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      `/professors/${id}/generate-profile`,
      {},
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async batchGenerateProfiles(ids: number[]): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      '/professors/batch-generate-profiles',
      { ids },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async startFillPublications(id: number): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      `/professors/${id}/fill-publications`,
      {},
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async batchRefresh(ids: number[]): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      '/professors/batch-refresh',
      { ids },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },
}
