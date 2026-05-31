/** ISO-8601 strings with explicit timezone (Z or ±offset). */
const HAS_TIMEZONE = /(?:Z|[+-]\d{2}:?\d{2})$/i

/**
 * Parse API datetime strings. Naive timestamps from the backend are UTC.
 */
export function parseApiDateTime(iso: string): Date {
  const trimmed = iso.trim()
  if (HAS_TIMEZONE.test(trimmed)) {
    return new Date(trimmed)
  }
  return new Date(`${trimmed}Z`)
}

export function formatDateTime(
  iso: string | null | undefined,
  locale: string
): string {
  if (!iso) return ''
  return parseApiDateTime(iso).toLocaleString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatRelativeTime(dateStr: string, locale: string): string {
  const date = parseApiDateTime(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  const diffHr = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)
  const isEn = locale === 'en-US'

  if (diffMin < 1) return isEn ? 'just now' : '刚刚'
  if (diffMin < 60) return isEn ? `${diffMin}m ago` : `${diffMin} 分钟前`
  if (diffHr < 24) return isEn ? `${diffHr}h ago` : `${diffHr} 小时前`
  if (diffDay < 7) return isEn ? `${diffDay}d ago` : `${diffDay} 天前`
  return date.toLocaleDateString(locale, { month: 'short', day: 'numeric' })
}
