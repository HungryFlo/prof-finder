import { useMessage } from 'naive-ui'

export function useApiError() {
  const message = useMessage()

  function handleApiError(error: unknown, fallback: string) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || fallback)
  }

  return { handleApiError }
}
