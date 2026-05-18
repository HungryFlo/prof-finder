<script setup lang="ts">
import { computed } from 'vue'
import {
  NConfigProvider,
  NMessageProvider,
  NDialogProvider,
  NNotificationProvider,
  darkTheme,
  zhCN,
  dateZhCN,
  enUS,
  dateEnUS,
} from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/composables/useTheme'

const { locale } = useI18n()
const { isDark } = useTheme()

const naiveLocale = computed(() => (locale.value === 'en' ? enUS : zhCN))
const naiveDateLocale = computed(() => (locale.value === 'en' ? dateEnUS : dateZhCN))
const baseTheme = computed(() => (isDark.value ? darkTheme : undefined))

const themeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: 'Geist, ui-sans-serif, system-ui, sans-serif',
    fontFamilyMono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
    fontWeight: '400',
    fontWeightStrong: '600',
    primaryColor: '#2f6f8f',
    primaryColorHover: '#285e78',
    primaryColorPressed: '#214d63',
    primaryColorSuppl: '#3d87ad',
    borderRadius: '10px',
    borderRadiusSmall: '8px',
    bodyColor: '#f2f5f8',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    hoverColor: 'rgba(47, 111, 143, 0.08)',
    borderColor: '#d8e0e8',
    textColor1: '#14232c',
    textColor2: '#2a3d49',
    textColor3: '#5a6d7a',
    cubicBezierEaseInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
  Button: {
    fontWeight: '500',
  },
}
</script>

<template>
  <n-config-provider
    :theme="baseTheme"
    :locale="naiveLocale"
    :date-locale="naiveDateLocale"
    :theme-overrides="themeOverrides"
  >
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <router-view />
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
body {
  margin: 0;
  padding: 0;
}
</style>
