import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'

const saved = localStorage.getItem('ui-locale')
const locale = saved === 'en' ? 'en' : 'zh'

function syncHtmlLang(lang: 'zh' | 'en') {
  document.documentElement.lang = lang
}

export const i18n = createI18n({
  legacy: false,
  locale,
  fallbackLocale: 'zh',
  messages: { zh, en },
})

syncHtmlLang(locale)

export function setLocale(lang: 'zh' | 'en') {
  i18n.global.locale.value = lang
  localStorage.setItem('ui-locale', lang)
  syncHtmlLang(lang)
}

export function getLocale(): 'zh' | 'en' {
  return i18n.global.locale.value as 'zh' | 'en'
}
