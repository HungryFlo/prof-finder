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
import type { SourceInput } from '@/types'

const props = defineProps<{
  modelValue: SourceInput[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: SourceInput[]): void
}>()

const message = useMessage()
const { t } = useI18n()

const arxivUrl = ref('')
const pdfInputRef = ref<HTMLInputElement | null>(null)
const uploadingPdf = ref(false)
const creatingArxiv = ref(false)

function updateItems(nextItems: SourceInput[]) {
  emit('update:modelValue', nextItems)
}

function openPdfPicker() {
  pdfInputRef.value?.click()
}

async function handlePdfChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploadingPdf.value = true
  try {
    const created = await sourceInputsApi.uploadPdf(file)
    updateItems([created, ...props.modelValue])
    message.success(t('source.pdfUploadedOk'))
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('source.pdfProcessFail'))
  } finally {
    uploadingPdf.value = false
    target.value = ''
  }
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
    if (created.metadata_only) {
      message.warning(t('source.metadataOnlyHint'))
    } else {
      message.success(t('source.arxivAddedOk'))
    }
    arxivUrl.value = ''
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('source.arxivAddFail'))
  } finally {
    creatingArxiv.value = false
  }
}

async function retryParse(item: SourceInput) {
  try {
    const updated = await sourceInputsApi.retryPdfParse(item.id)
    const nextItems = props.modelValue.map((entry) => (entry.id === item.id ? updated : entry))
    updateItems(nextItems)
    if (updated.metadata_only) {
      message.warning(t('source.retryParseFailedSoon'))
    } else {
      message.success(t('source.retryParseOk'))
    }
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('source.retryParseFail'))
  }
}
</script>

<template>
  <n-card :title="$t('source.title')" size="small">
    <n-space vertical>
      <n-space align="center">
        <input
          ref="pdfInputRef"
          type="file"
          accept="application/pdf"
          tabindex="-1"
          aria-hidden="true"
          style="position: absolute; width: 0; height: 0; opacity: 0; overflow: hidden"
          :disabled="uploadingPdf"
          @change="handlePdfChange"
        />
        <n-button :disabled="uploadingPdf" @click="openPdfPicker">{{ $t('source.uploadPdf') }}</n-button>
        <slot name="actions" />
        <n-tag v-if="uploadingPdf" type="info">{{ $t('source.processingPdfTag') }}</n-tag>
      </n-space>

      <n-space>
        <n-input
          v-model:value="arxivUrl"
          :placeholder="$t('source.arxivPlaceholder')"
          style="width: 420px"
        />
        <n-button type="primary" :loading="creatingArxiv" @click="handleAddArxiv">{{ $t('source.addArxiv') }}</n-button>
      </n-space>

      <n-list bordered>
        <n-list-item v-for="item in modelValue" :key="item.id">
          <n-space vertical style="width: 100%">
            <n-space justify="space-between">
              <n-space>
                <n-tag type="info">{{ item.source_type }}</n-tag>
                <n-tag v-if="item.metadata_only" type="warning">metadata-only</n-tag>
                <n-tag v-if="item.status === 'succeeded'" type="success">{{ $t('source.succeeded') }}</n-tag>
                <n-tag v-else-if="item.status === 'failed'" type="error">{{ $t('source.failed') }}</n-tag>
                <n-tag v-else type="default">{{ item.status }}</n-tag>
              </n-space>
              <n-button
                v-if="item.source_type === 'arxiv' && item.metadata_only"
                size="small"
                @click="retryParse(item)"
              >
                {{ $t('source.retryParse') }}
              </n-button>
            </n-space>

            <div v-if="item.title"><strong>{{ item.title }}</strong></div>
            <div v-if="item.source_url">{{ item.source_url }}</div>
            <n-alert v-if="item.error_message" type="warning" :show-icon="false">
              {{ item.error_message }}
            </n-alert>
          </n-space>
        </n-list-item>
      </n-list>
    </n-space>
  </n-card>
</template>
