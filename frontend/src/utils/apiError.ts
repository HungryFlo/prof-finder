import type { AxiosError } from 'axios'
import type { ComposerTranslation } from 'vue-i18n'

export interface ParsedApiError {
  code: string | null
  detail: string
  status: number | null
  /** True when there is something useful to show in the details modal. */
  hasRawDetail: boolean
}

type TranslateFn = ComposerTranslation
type TeFn = (key: string) => boolean

function formatLegacyDetail(detail: unknown): string {
  if (detail == null) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'object' && item) {
          const msg = (item as { msg?: string }).msg
          return msg || JSON.stringify(item)
        }
        return String(item)
      })
      .join('; ')
  }
  if (typeof detail === 'object') {
    const obj = detail as { code?: string; detail?: string; message?: string }
    if (typeof obj.detail === 'string') return obj.detail
    if (typeof obj.message === 'string') return obj.message
    return JSON.stringify(detail)
  }
  return String(detail)
}

function extractCode(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null
  const obj = data as { code?: unknown; detail?: unknown }
  if (typeof obj.code === 'string' && obj.code) return obj.code
  if (typeof obj.detail === 'object' && obj.detail) {
    const nested = obj.detail as { code?: unknown }
    if (typeof nested.code === 'string' && nested.code) return nested.code
  }
  if (typeof obj.detail === 'string' && /^[A-Z][A-Z0-9_]+$/.test(obj.detail)) {
    return obj.detail
  }
  return null
}

/** Parse Axios / fetch / unknown errors into a normalized shape. */
export function parseApiError(error: unknown): ParsedApiError {
  const axiosErr = error as AxiosError<{ code?: string; detail?: unknown }>
  const status = axiosErr.response?.status ?? null
  const data = axiosErr.response?.data

  if (data !== undefined) {
    const code = extractCode(data)
    let detail = ''
    if (data && typeof data === 'object' && 'detail' in data) {
      detail = formatLegacyDetail((data as { detail: unknown }).detail)
    } else if (typeof data === 'string') {
      detail = data
    }
    if (!detail && code) detail = code
    return {
      code,
      detail: detail || axiosErr.message || '',
      status,
      hasRawDetail: Boolean(detail || code || status),
    }
  }

  // Network / timeout (no response)
  const code = (error as { code?: string })?.code
  if (code === 'ECONNABORTED' || code === 'ERR_NETWORK' || axiosErr.message === 'Network Error') {
    return {
      code: 'NETWORK_ERROR',
      detail: axiosErr.message || 'Network Error',
      status: null,
      hasRawDetail: true,
    }
  }

  if (error instanceof Error) {
    return {
      code: null,
      detail: error.message,
      status: null,
      hasRawDetail: Boolean(error.message),
    }
  }

  return {
    code: null,
    detail: String(error ?? ''),
    status: null,
    hasRawDetail: Boolean(error),
  }
}

function statusFallbackKey(status: number | null): string | null {
  if (status === 401) return 'common.unauthorized'
  if (status === 403) return 'errors.FORBIDDEN'
  if (status === 404) return 'errors.NOT_FOUND'
  if (status === 409) return 'errors.CONFLICT'
  if (status === 422) return 'errors.VALIDATION_ERROR'
  if (status === 503) return 'errors.SERVICE_UNAVAILABLE'
  if (status != null && status >= 500) return 'errors.INTERNAL_ERROR'
  return null
}

/** Resolve a localized friendly message; never returns raw backend prose as the primary text. */
export function resolveFriendlyMessage(
  parsed: ParsedApiError,
  t: TranslateFn,
  te: TeFn,
  actionFallback: string,
): string {
  if (parsed.code === 'NETWORK_ERROR') {
    return t('common.networkError')
  }
  if (parsed.code) {
    const key = `errors.${parsed.code}`
    if (te(key)) return t(key)
  }
  const statusKey = statusFallbackKey(parsed.status)
  if (statusKey && te(statusKey)) return t(statusKey)
  if (actionFallback) return actionFallback
  return t('common.unknownError')
}

export function formatErrorDetailText(parsed: ParsedApiError, friendlyMessage?: string): string {
  const lines: string[] = []
  if (friendlyMessage) lines.push(`Message: ${friendlyMessage}`)
  if (parsed.code) lines.push(`Code: ${parsed.code}`)
  if (parsed.status != null) lines.push(`HTTP: ${parsed.status}`)
  if (parsed.detail) lines.push(`Detail: ${parsed.detail}`)
  return lines.join('\n')
}
