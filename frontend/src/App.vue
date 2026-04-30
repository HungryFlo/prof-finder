<script setup lang="ts">
import { computed } from 'vue'
import { NConfigProvider, NMessageProvider, NDialogProvider, NNotificationProvider, zhCN, dateZhCN, enUS, dateEnUS } from 'naive-ui'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const naiveLocale = computed(() => locale.value === 'en' ? enUS : zhCN)
const naiveDateLocale = computed(() => locale.value === 'en' ? dateEnUS : dateZhCN)
</script>

<template>
  <n-config-provider :locale="naiveLocale" :date-locale="naiveDateLocale">
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
