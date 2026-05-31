import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDateTime, formatRelativeTime } from '@/utils/datetime'

export function useDateLocale() {
  const { locale } = useI18n()
  return computed(() => (locale.value === 'en' ? 'en-US' : 'zh-CN'))
}

export function useFormatDate() {
  const dateLocale = useDateLocale()
  return {
    dateLocale,
    formatDateTime: (iso: string | null | undefined) =>
      formatDateTime(iso, dateLocale.value),
    formatRelativeTime: (iso: string) =>
      formatRelativeTime(iso, dateLocale.value),
  }
}
