import client from './client'
import type { Profile, ProfileCreate } from '@/types'

export interface ProfileUploadResponse {
  parsed_data: ProfileCreate
  message: string
}

export const profilesApi = {
  async list(): Promise<Profile[]> {
    const response = await client.get<Profile[]>('/profiles')
    return response.data
  },

  async create(data: ProfileCreate): Promise<Profile> {
    const response = await client.post<Profile>('/profiles', data)
    return response.data
  },

  async upload(file: File, title: string, useLlm: boolean = true): Promise<ProfileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', title)
    formData.append('use_llm', String(useLlm))
    
    const response = await client.post<ProfileUploadResponse>('/profiles/upload', formData, {
      // Resume parsing (especially with LLM) can take longer than default API calls.
      timeout: 120000,
    })
    return response.data
  },

  async get(id: number): Promise<Profile> {
    const response = await client.get<Profile>(`/profiles/${id}`)
    return response.data
  },

  async update(id: number, data: Partial<ProfileCreate>): Promise<Profile> {
    const response = await client.put<Profile>(`/profiles/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<{ message: string }> {
    const response = await client.delete<{ message: string }>(`/profiles/${id}`)
    return response.data
  },

  async activate(id: number): Promise<Profile> {
    const response = await client.post<Profile>(`/profiles/${id}/activate`)
    return response.data
  },

  async batchDelete(ids: number[]): Promise<{ message: string }> {
    const response = await client.post<{ message: string }>('/profiles/batch-delete', { ids })
    return response.data
  },
}
