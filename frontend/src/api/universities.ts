import client from './client'

export interface University {
  id: number
  full_name: string
  name_variants: string[]
  created_at: string
  updated_at: string
}

export interface UniversityCreate {
  full_name: string
}

export interface UniversityUpdate {
  full_name?: string
  name_variants?: string[]
}

export const universitiesApi = {
  async list(): Promise<University[]> {
    const response = await client.get<University[]>('/universities')
    return response.data
  },

  async create(data: UniversityCreate): Promise<University> {
    const response = await client.post<University>('/universities', data, {
      timeout: 60_000, // LLM call may take time
    })
    return response.data
  },

  async get(id: number): Promise<University> {
    const response = await client.get<University>(`/universities/${id}`)
    return response.data
  },

  async update(id: number, data: UniversityUpdate): Promise<University> {
    const response = await client.put<University>(`/universities/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<{ message: string }> {
    const response = await client.delete<{ message: string }>(`/universities/${id}`)
    return response.data
  },
}
