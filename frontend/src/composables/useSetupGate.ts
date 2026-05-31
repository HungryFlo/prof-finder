import { ref } from 'vue'
import { setupApi, type SetupStatus } from '@/api/setup'

const status = ref<SetupStatus | null>(null)
let loadPromise: Promise<SetupStatus> | null = null

export function useSetupGate() {
  async function ensureStatus(): Promise<SetupStatus> {
    if (status.value) {
      return status.value
    }
    if (!loadPromise) {
      loadPromise = setupApi.getStatus().then((value) => {
        status.value = value
        return value
      })
    }
    return loadPromise
  }

  function resetStatus(): void {
    status.value = null
    loadPromise = null
  }

  async function requiresSetup(): Promise<boolean> {
    const current = await ensureStatus()
    return current.packaged && !current.configured
  }

  return {
    status,
    ensureStatus,
    resetStatus,
    requiresSetup,
  }
}
