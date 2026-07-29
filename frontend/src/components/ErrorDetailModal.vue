<script setup lang="ts">
import { computed } from 'vue'
import { NModal, NButton, NSpace, NText, useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { storeToRefs } from 'pinia'
import { useErrorDetailStore } from '@/stores/errorDetail'
import { formatErrorDetailText } from '@/utils/apiError'

const { t } = useI18n()
const message = useMessage()
const store = useErrorDetailStore()
const { show, payload } = storeToRefs(store)

const detailText = computed(() => {
  if (!payload.value) return ''
  return formatErrorDetailText(payload.value, payload.value.friendlyMessage)
})

async function copyDetail() {
  try {
    await navigator.clipboard.writeText(detailText.value)
    message.success(t('common.copySuccess'))
  } catch {
    message.error(t('common.copyFailed'))
  }
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    :title="t('common.errorDetailsTitle')"
    style="width: min(560px, 92vw)"
    :bordered="false"
    @update:show="(v) => { if (!v) store.close() }"
  >
    <template v-if="payload">
      <p style="margin: 0 0 12px; line-height: 1.5">
        {{ payload.friendlyMessage }}
      </p>
      <n-space vertical :size="6" style="margin-bottom: 12px">
        <n-text v-if="payload.code" depth="3">
          {{ t('common.errorCode') }}: {{ payload.code }}
        </n-text>
        <n-text v-if="payload.status != null" depth="3">
          {{ t('common.errorStatus') }}: {{ payload.status }}
        </n-text>
      </n-space>
      <pre class="error-detail-pre">{{ payload.detail || t('common.noErrorDetail') }}</pre>
    </template>
    <template #footer>
      <n-space justify="end">
        <n-button @click="copyDetail">{{ t('common.copyDetail') }}</n-button>
        <n-button type="primary" @click="store.close()">{{ t('common.close') }}</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<style scoped>
.error-detail-pre {
  margin: 0;
  padding: 12px;
  max-height: 280px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.5;
  border-radius: 8px;
  background: var(--n-color-embedded, rgba(127, 127, 127, 0.08));
}
</style>
