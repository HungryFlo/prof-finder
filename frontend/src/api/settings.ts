import client from './client'
import type { UserSettings } from '@/types'

export interface SettingsUpdate {
  llm_provider?: 'openai' | 'anthropic'
  llm_api_key?: string
  llm_base_url?: string
  llm_model?: string
  request_delay?: number
  auto_enrich_on_save_fetch_publication_details?: boolean
  auto_enrich_on_save_paper_summaries?: boolean
  auto_enrich_on_save_research_profile?: boolean
}

export const settingsApi = {
  async get(): Promise<UserSettings> {
    const response = await client.get<UserSettings>('/settings')
    return response.data
  },

  async update(data: SettingsUpdate): Promise<UserSettings> {
    const response = await client.put<UserSettings>('/settings', data)
    return response.data
  },
}
