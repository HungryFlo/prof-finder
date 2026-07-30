import client from './client'
import { getLocale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import type { ChatMessage, Profile, ProfileCreate, ProfileChatResponse } from '@/types'
import type { TaskStartResponse } from '@/api/tasks'

export interface ProfileMaterialUploadOptions {
  useLlm?: boolean
  researchInterests?: string
  personalStatement?: string
  researchPlan?: string
  notes?: string
  experiencePoolId?: number | null
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
    if (options.experiencePoolId != null) {
      formData.append('experience_pool_id', String(options.experiencePoolId))
    }
    
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

  async chatStream(
    profileId: number,
    message: string,
    history: ChatMessage[],
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (error: { code?: string; detail: string; status?: number }) => void,
    signal?: AbortSignal,
  ): Promise<void> {
    const authStore = useAuthStore()
    const token = authStore.accessToken ?? ''
    const url = `/api/profiles/${profileId}/chat/stream?token=${encodeURIComponent(token)}`

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history, locale: getLocale() }),
      signal,
    })

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({} as Record<string, unknown>))
      const code = typeof errBody.code === 'string' ? errBody.code : undefined
      const detail =
        typeof errBody.detail === 'string'
          ? errBody.detail
          : code || 'Chat request failed'
      onError({ code, detail, status: response.status })
      return
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let currentEvent = 'message'

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const rawLine of lines) {
          const line = rawLine.endsWith('\r') ? rawLine.slice(0, -1) : rawLine
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (currentEvent === 'token') {
              onToken(data)
            } else if (currentEvent === 'done') {
              onDone()
            } else if (currentEvent === 'error') {
              onError({ detail: data })
            }
          }
          if (line === '') {
            currentEvent = 'message'
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      throw err
    }
  },
}
