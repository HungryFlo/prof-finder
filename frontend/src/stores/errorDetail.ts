import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ParsedApiError } from '@/utils/apiError'

export interface ErrorDetailPayload extends ParsedApiError {
  friendlyMessage: string
}

export const useErrorDetailStore = defineStore('errorDetail', () => {
  const show = ref(false)
  const payload = ref<ErrorDetailPayload | null>(null)

  function open(next: ErrorDetailPayload) {
    payload.value = next
    show.value = true
  }

  function openRaw(options: {
    friendlyMessage: string
    detail: string
    code?: string | null
    status?: number | null
  }) {
    open({
      friendlyMessage: options.friendlyMessage,
      detail: options.detail,
      code: options.code ?? null,
      status: options.status ?? null,
      hasRawDetail: Boolean(options.detail || options.code || options.status),
    })
  }

  function close() {
    show.value = false
  }

  return { show, payload, open, openRaw, close }
})
