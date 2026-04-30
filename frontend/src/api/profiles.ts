import client from './client'
import { getLocale } from '@/i18n'
import type { ChatMessage, Profile, ProfileCreate, ProfileChatResponse } from '@/types'
import type { TaskStartResponse } from '@/api/tasks'

export interface ProfileMaterialUploadOptions {
  useLlm?: boolean
  researchInterests?: string
  personalStatement?: string
  researchPlan?: string
  notes?: string
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

  async upload(
    files: File[],
    title: string,
    options: ProfileMaterialUploadOptions = {}
  ): Promise<TaskStartResponse> {
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    formData.append('title', title)
    formData.append('use_llm', String(options.useLlm ?? true))
    formData.append('research_interests', options.researchInterests ?? '')
    formData.append('personal_statement', options.personalStatement ?? '')
    formData.append('research_plan', options.researchPlan ?? '')
    formData.append('notes', options.notes ?? '')
    
    const response = await client.post<TaskStartResponse>('/profiles/upload', formData)
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

  async chat(
    profileId: number,
    message: string,
    history: ChatMessage[]
  ): Promise<ProfileChatResponse> {
    const response = await client.post<ProfileChatResponse>(`/profiles/${profileId}/chat`, {
      message,
      history,
      locale: getLocale(),
    })
    return response.data
  },

  async refineFromChat(profileId: number, history: ChatMessage[]): Promise<TaskStartResponse> {
    const response = await client.post<TaskStartResponse>(`/profiles/${profileId}/chat/refine`, { history })
    return response.data
  },
}
