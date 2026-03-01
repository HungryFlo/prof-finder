<script setup lang="ts">
import { ref } from 'vue'
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
const arxivUrl = ref('')
const uploadingPdf = ref(false)
const creatingArxiv = ref(false)

function updateItems(nextItems: SourceInput[]) {
  emit('update:modelValue', nextItems)
}

async function handlePdfChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploadingPdf.value = true
  try {
    const created = await sourceInputsApi.uploadPdf(file)
    updateItems([created, ...props.modelValue])
    message.success('PDF 上传并解析成功')
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || 'PDF 处理失败')
  } finally {
    uploadingPdf.value = false
    target.value = ''
  }
}

async function handleAddArxiv() {
  if (!arxivUrl.value.trim()) {
    message.warning('请输入 ArXiv 链接')
    return
  }
  creatingArxiv.value = true
  try {
    const created = await sourceInputsApi.createFromArxiv(arxivUrl.value.trim())
    updateItems([created, ...props.modelValue])
    if (created.metadata_only) {
      message.warning('已保存元数据，稍后可重试 PDF 解析')
    } else {
      message.success('ArXiv 来源已添加')
    }
    arxivUrl.value = ''
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || 'ArXiv 添加失败')
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
      message.warning('重试失败，请稍后再试')
    } else {
      message.success('重试解析成功')
    }
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '重试失败')
  }
}
</script>

<template>
  <n-card title="来源输入（PDF / ArXiv）" size="small">
    <n-space vertical>
      <n-space>
        <label>
          <input type="file" accept="application/pdf" :disabled="uploadingPdf" @change="handlePdfChange" />
        </label>
        <slot name="actions" />
        <n-tag v-if="uploadingPdf" type="info">PDF 处理中...</n-tag>
      </n-space>

      <n-space>
        <n-input
          v-model:value="arxivUrl"
          placeholder="https://arxiv.org/abs/xxxx.xxxxx"
          style="width: 420px"
        />
        <n-button type="primary" :loading="creatingArxiv" @click="handleAddArxiv">添加 ArXiv</n-button>
      </n-space>

      <n-list bordered>
        <n-list-item v-for="item in modelValue" :key="item.id">
          <n-space vertical style="width: 100%">
            <n-space justify="space-between">
              <n-space>
                <n-tag type="info">{{ item.source_type }}</n-tag>
                <n-tag v-if="item.metadata_only" type="warning">metadata-only</n-tag>
                <n-tag v-if="item.status === 'succeeded'" type="success">succeeded</n-tag>
                <n-tag v-else-if="item.status === 'failed'" type="error">failed</n-tag>
                <n-tag v-else type="default">{{ item.status }}</n-tag>
              </n-space>
              <n-button
                v-if="item.source_type === 'arxiv' && item.metadata_only"
                size="small"
                @click="retryParse(item)"
              >
                重试 PDF 解析
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
