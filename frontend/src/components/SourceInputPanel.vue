<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NAlert,
  NButton,
  NCard,
  NInput,
  NList,
  NListItem,
  NSpace,
  NTag,
  useMessage,
} from 'naive-ui'
import { sourceInputsApi } from '@/api/source-inputs'
import { useApiError } from '@/composables/useApiError'
import { useErrorDetailStore } from '@/stores/errorDetail'
import type { SourceInput } from '@/types'

const props = defineProps<{
  modelValue: SourceInput[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: SourceInput[]): void
}>()

const message = useMessage()
const { t } = useI18n()
const { handleApiError } = useApiError()
const errorDetail = useErrorDetailStore()

const arxivUrl = ref('')
const creatingArxiv = ref(false)

function updateItems(nextItems: SourceInput[]) {
  emit('update:modelValue', nextItems)
}

function showSourceError(item: SourceInput) {
  if (!item.error_message) return
  errorDetail.openRaw({
    friendlyMessage: t('source.failed'),
    detail: item.error_message,
  })
}

async function handleAddArxiv() {
  if (!arxivUrl.value.trim()) {
    message.warning(t('source.needArxivUrl'))
    return
  }
  creatingArxiv.value = true
  try {
    const created = await sourceInputsApi.createFromArxiv(arxivUrl.value.trim())
    updateItems([created, ...props.modelValue])
    message.success(t('source.arxivAddedOk'))
    arxivUrl.value = ''
  } catch (error: unknown) {
    handleApiError(error, t('source.arxivAddFail'))
  } finally {
    creatingArxiv.value = false
  }
}
</script>

<template>
  <n-card :title="$t('source.title')" size="small">
    <n-space vertical>
      <n-space>
        <n-input
          v-model:value="arxivUrl"
          :placeholder="$t('source.arxivPlaceholder')"
          style="width: 420px"
        />
        <n-button type="primary" :loading="creatingArxiv" @click="handleAddArxiv">{{ $t('source.addArxiv') }}</n-button>
        <slot name="actions" />
      </n-space>

      <n-list bordered>
        <n-list-item v-for="item in modelValue" :key="item.id">
          <n-space vertical style="width: 100%">
            <n-space>
              <n-tag type="info">{{ item.source_type }}</n-tag>
              <n-tag v-if="item.status === 'succeeded'" type="success">{{ $t('source.succeeded') }}</n-tag>
              <n-tag v-else-if="item.status === 'failed'" type="error">{{ $t('source.failed') }}</n-tag>
              <n-tag v-else type="default">{{ item.status }}</n-tag>
            </n-space>

            <div v-if="item.title"><strong>{{ item.title }}</strong></div>
            <div v-if="item.source_url">{{ item.source_url }}</div>
            <n-alert v-if="item.error_message" type="warning" :show-icon="false">
              <n-space align="center" justify="space-between" style="width: 100%">
                <span>{{ $t('source.failed') }}</span>
                <n-button text type="primary" size="tiny" @click="showSourceError(item)">
                  {{ $t('common.errorDetails') }}
                </n-button>
              </n-space>
            </n-alert>
          </n-space>
        </n-list-item>
      </n-list>
    </n-space>
  </n-card>
</template>
