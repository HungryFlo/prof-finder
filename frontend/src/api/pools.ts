import client from './client'
import type {
  CompositionDocType,
  ExperienceCluster,
  ExperiencePool,
  ExperienceSeed,
  ExperienceStory,
  PoolComposition,
  PoolPhase,
  SeedStatus,
} from '@/types'

export const poolsApi = {
  async list(): Promise<ExperiencePool[]> {
    const response = await client.get<ExperiencePool[]>('/pools')
    return response.data
  },

  async create(data: { title: string; description?: string }): Promise<ExperiencePool> {
    const response = await client.post<ExperiencePool>('/pools', data)
    return response.data
  },

  async get(id: number): Promise<ExperiencePool> {
    const response = await client.get<ExperiencePool>(`/pools/${id}`)
    return response.data
  },

  async update(
    id: number,
    data: { title?: string; description?: string; phase?: PoolPhase }
  ): Promise<ExperiencePool> {
    const response = await client.put<ExperiencePool>(`/pools/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<{ message: string }> {
    const response = await client.delete<{ message: string }>(`/pools/${id}`)
    return response.data
  },

  async listSeeds(poolId: number, status?: SeedStatus): Promise<ExperienceSeed[]> {
    const response = await client.get<ExperienceSeed[]>(`/pools/${poolId}/seeds`, {
      params: status ? { status_filter: status } : undefined,
    })
    return response.data
  },

  async createSeed(
    poolId: number,
    data: { content: string; tags?: string[] }
  ): Promise<ExperienceSeed> {
    const response = await client.post<ExperienceSeed>(`/pools/${poolId}/seeds`, data)
    return response.data
  },

  async createSeedsBatch(poolId: number, contents: string[]): Promise<ExperienceSeed[]> {
    const response = await client.post<ExperienceSeed[]>(`/pools/${poolId}/seeds/batch`, {
      contents,
    })
    return response.data
  },

  async updateSeed(
    poolId: number,
    seedId: number,
    data: {
      content?: string
      status?: SeedStatus
      cluster_id?: number | null
      standalone?: boolean
      sort_order?: number
      tags?: string[]
      clear_cluster?: boolean
    }
  ): Promise<ExperienceSeed> {
    const response = await client.put<ExperienceSeed>(
      `/pools/${poolId}/seeds/${seedId}`,
      data
    )
    return response.data
  },

  async deleteSeed(poolId: number, seedId: number): Promise<{ message: string }> {
    const response = await client.delete<{ message: string }>(
      `/pools/${poolId}/seeds/${seedId}`
    )
    return response.data
  },

  async listClusters(poolId: number): Promise<ExperienceCluster[]> {
    const response = await client.get<ExperienceCluster[]>(`/pools/${poolId}/clusters`)
    return response.data
  },

  async createCluster(
    poolId: number,
    data: { title: string; note?: string; color?: string }
  ): Promise<ExperienceCluster> {
    const response = await client.post<ExperienceCluster>(`/pools/${poolId}/clusters`, data)
    return response.data
  },

  async updateCluster(
    poolId: number,
    clusterId: number,
    data: { title?: string; note?: string; color?: string; sort_order?: number }
  ): Promise<ExperienceCluster> {
    const response = await client.put<ExperienceCluster>(
      `/pools/${poolId}/clusters/${clusterId}`,
      data
    )
    return response.data
  },

  async deleteCluster(poolId: number, clusterId: number): Promise<{ message: string }> {
    const response = await client.delete<{ message: string }>(
      `/pools/${poolId}/clusters/${clusterId}`
    )
    return response.data
  },

  async mergeClusters(
    poolId: number,
    sourceClusterId: number,
    targetClusterId: number
  ): Promise<ExperienceCluster> {
    const response = await client.post<ExperienceCluster>(`/pools/${poolId}/clusters/merge`, {
      source_cluster_id: sourceClusterId,
      target_cluster_id: targetClusterId,
    })
    return response.data
  },

  async listStories(poolId: number): Promise<ExperienceStory[]> {
    const response = await client.get<ExperienceStory[]>(`/pools/${poolId}/stories`)
    return response.data
  },

  async updateStory(
    poolId: number,
    seedId: number,
    data: Partial<
      Pick<
        ExperienceStory,
        | 'origin'
        | 'process'
        | 'outcome'
        | 'problems'
        | 'setbacks'
        | 'knowledge'
        | 'insights'
        | 'freeform'
      >
    >
  ): Promise<ExperienceStory> {
    const response = await client.put<ExperienceStory>(
      `/pools/${poolId}/stories/${seedId}`,
      data
    )
    return response.data
  },

  async listCompositions(poolId: number): Promise<PoolComposition[]> {
    const response = await client.get<PoolComposition[]>(`/pools/${poolId}/compositions`)
    return response.data
  },

  async createComposition(
    poolId: number,
    data: {
      doc_type: CompositionDocType
      title: string
      body?: string
      source_story_ids?: number[]
    }
  ): Promise<PoolComposition> {
    const response = await client.post<PoolComposition>(
      `/pools/${poolId}/compositions`,
      data
    )
    return response.data
  },

  async updateComposition(
    poolId: number,
    compositionId: number,
    data: {
      doc_type?: CompositionDocType
      title?: string
      body?: string
      source_story_ids?: number[]
    }
  ): Promise<PoolComposition> {
    const response = await client.put<PoolComposition>(
      `/pools/${poolId}/compositions/${compositionId}`,
      data
    )
    return response.data
  },

  async deleteComposition(
    poolId: number,
    compositionId: number
  ): Promise<{ message: string }> {
    const response = await client.delete<{ message: string }>(
      `/pools/${poolId}/compositions/${compositionId}`
    )
    return response.data
  },

  async generateComposition(
    poolId: number,
    data: {
      doc_type: CompositionDocType
      story_ids: number[]
      title?: string
      language?: 'zh' | 'en'
    }
  ): Promise<PoolComposition> {
    const response = await client.post<PoolComposition>(
      `/pools/${poolId}/compositions/generate`,
      data
    )
    return response.data
  },

  async applyComposition(
    poolId: number,
    compositionId: number,
    profileId: number
  ): Promise<{ message: string }> {
    const response = await client.post<{ message: string }>(
      `/pools/${poolId}/compositions/${compositionId}/apply`,
      { profile_id: profileId }
    )
    return response.data
  },
}
