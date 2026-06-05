import client from './client'
import type {
  Professor,
  PaperSummary,
  ProfessorListItem,
  DblpSearchResult,
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

export interface CrawlerConfigResponse {
  id: number
  name: string
  university: string
  department: string | null
  list_url: string
  extraction_mode: 'css' | 'llm'
  css_selectors: Record<string, string | null> | null
  affiliation: string | null
  is_builtin: boolean
  builtin_crawler_id: string | null
  university_id: number | null
  created_at: string
  updated_at: string
}

export interface CrawlerConfigCreate {
  name: string
  university: string
  department?: string | null
  list_url: string
  extraction_mode: 'css' | 'llm'
  css_selectors?: Record<string, string | null> | null
  affiliation?: string | null
  university_id?: number | null
}

export interface CrawlerTestRequest {
  list_url: string
  extraction_mode: 'css' | 'llm'
  css_selectors?: Record<string, string | null> | null
  affiliation?: string | null
  name?: string | null
  university?: string | null
  department?: string | null
}

export interface CrawlerTestResponse {
  success: boolean
  sample_results: Record<string, unknown>[]
  total_found: number
  error_message: string | null
  cache_key: string | null
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
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export const professorsApi = {
  async list(params: ProfessorListParams = {}): Promise<PaginatedResponse<ProfessorListItem>> {
    const response = await client.get<PaginatedResponse<ProfessorListItem>>('/professors', {
      params: {
        page: params.page || 1,
        page_size: params.page_size || 20,
        affiliation: params.affiliation || undefined,
        interest: params.interest || undefined,
        search: params.search || undefined,
        sort_by: params.sort_by || undefined,
        sort_order: params.sort_order || undefined,
      },
    })
    return response.data
  },

  async getAffiliations(): Promise<string[]> {
    const response = await client.get<string[]>('/professors/affiliations')
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

  async get(id: number): Promise<Professor> {
    const response = await client.get<Professor>(`/professors/${id}`, {
      timeout: POST_BEHIND_SSE_TIMEOUT_MS,
    })
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

  async crawlHomepage(id: number): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      `/professors/${id}/crawl-homepage`,
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

  // ---- Crawler Config CRUD ----

  async getCrawlerConfigs(): Promise<CrawlerConfigResponse[]> {
    const response = await client.get<CrawlerConfigResponse[]>('/professors/crawler-configs')
    return response.data
  },

  async createCrawlerConfig(data: CrawlerConfigCreate): Promise<CrawlerConfigResponse> {
    const response = await client.post<CrawlerConfigResponse>('/professors/crawler-configs', data)
    return response.data
  },

  async updateCrawlerConfig(
    id: number,
    data: Partial<CrawlerConfigCreate>
  ): Promise<CrawlerConfigResponse> {
    const response = await client.put<CrawlerConfigResponse>(
      `/professors/crawler-configs/${id}`,
      data
    )
    return response.data
  },

  async deleteCrawlerConfig(id: number): Promise<{ message: string }> {
    const response = await client.delete<{ message: string }>(
      `/professors/crawler-configs/${id}`
    )
    return response.data
  },

  async testCrawlerConfig(data: CrawlerTestRequest): Promise<CrawlerTestResponse> {
    const response = await client.post<CrawlerTestResponse>(
      '/professors/crawler-configs/test',
      data,
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async crawlWithConfig(configId: number, cacheKey?: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      '/professors/crawl-configured',
      { config_id: configId, cache_key: cacheKey || undefined },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async setScholarId(professorId: number, url: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      `/professors/${professorId}/set-scholar`,
      { url },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async searchDblp(query: string, limit: number = 10): Promise<DblpSearchResult[]> {
    const response = await client.post<DblpSearchResult[]>('/professors/dblp/search', {
      query,
      limit,
    })
    return response.data
  },

  async addByDblp(url: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      '/professors/dblp',
      { url },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async matchDblp(professorId: number): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      `/professors/${professorId}/match-dblp`,
      {},
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async confirmDblp(professorId: number, dblpPid: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      '/professors/confirm-dblp',
      { professor_id: professorId, dblp_pid: dblpPid },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async setDblp(professorId: number, url: string): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      `/professors/${professorId}/set-dblp`,
      { url },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async refreshDblp(id: number): Promise<Professor> {
    const response = await client.post<Professor>(
      `/professors/${id}/refresh-dblp`,
      {},
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async batchRefreshDblp(ids: number[]): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      '/professors/batch-refresh-dblp',
      { ids },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },

  async batchRefreshExternal(ids: number[]): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(
      '/professors/batch-refresh-external',
      { ids },
      { timeout: POST_BEHIND_SSE_TIMEOUT_MS }
    )
    return response.data
  },
}
