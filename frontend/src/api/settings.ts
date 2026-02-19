import client from './client'
import type { UserSettings } from '@/types'

export interface SettingsUpdate {
  deepseek_api_key?: string
  deepseek_base_url?: string
  request_delay?: number
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
