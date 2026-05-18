import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export function useDateLocale() {
  const { locale } = useI18n()
  return computed(() => (locale.value === 'en' ? 'en-US' : 'zh-CN'))
}
