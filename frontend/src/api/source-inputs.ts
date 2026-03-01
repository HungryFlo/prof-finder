import client from './client'
import type { SourceInput } from '@/types'

export const sourceInputsApi = {
  async listByProfessor(professorId: number): Promise<SourceInput[]> {
    const response = await client.get<SourceInput[]>('/source-inputs', {
      params: { professor_id: professorId },
    })
    return response.data
  },

  async uploadPdf(file: File): Promise<SourceInput> {
    const form = new FormData()
    form.append('file', file)
    const response = await client.post<SourceInput>('/source-inputs/pdf', form, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async createFromArxiv(url: string): Promise<SourceInput> {
    const response = await client.post<SourceInput>('/source-inputs/arxiv', { url })
    return response.data
  },

  async get(id: number): Promise<SourceInput> {
    const response = await client.get<SourceInput>(`/source-inputs/${id}`)
    return response.data
  },

  async retryPdfParse(id: number): Promise<SourceInput> {
    const response = await client.post<SourceInput>(`/source-inputs/${id}/retry-pdf-parse`)
    return response.data
  },
}
