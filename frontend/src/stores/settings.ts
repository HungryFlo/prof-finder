import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi, type SettingsUpdate } from '@/api/settings'
import type { UserSettings } from '@/types'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<UserSettings | null>(null)
  const loading = ref(false)
  let fetchPromise: Promise<UserSettings> | null = null

  async function fetchSettings(): Promise<UserSettings> {
    // Deduplicate concurrent fetches
    if (fetchPromise) return fetchPromise
    loading.value = true
    fetchPromise = settingsApi
      .get()
      .then((data) => {
        settings.value = data
        return data
      })
      .finally(() => {
        loading.value = false
        fetchPromise = null
      })
    return fetchPromise
  }

  async function updateSettings(data: SettingsUpdate): Promise<UserSettings> {
    const updated = await settingsApi.update(data)
    settings.value = updated
    return updated
  }

  function clearSettings() {
    settings.value = null
  }

  return {
    settings,
    loading,
    fetchSettings,
    updateSettings,
    clearSettings,
  }
})
