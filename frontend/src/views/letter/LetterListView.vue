<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NCard,
  NSpace,
  NButton,
  NDataTable,
  NTag,
  NModal,
  NInput,
  NPagination,
  NSelect,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { lettersApi } from '@/api/letters'
import { useTaskStore } from '@/stores/tasks'
import type { Letter, PaginatedResponse } from '@/types'

const message = useMessage()
const taskStore = useTaskStore()
const { t, locale } = useI18n()

const dateLocale = computed(() => (locale.value === 'en' ? 'en-US' : 'zh-CN'))

const loading = ref(false)
const data = ref<PaginatedResponse<Letter>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  pages: 1,
})
const currentPage = ref(1)

const showLetterModal = ref(false)
const currentLetter = ref<Letter | null>(null)
const editContent = ref('')
const saving = ref(false)

const letterLanguage = ref<'zh' | 'en'>('zh')
const letterLangOptions = computed(() => [
  { label: '中文', value: 'zh' as const },
  { label: 'English', value: 'en' as const },
])

function fmtDate(iso: string | null | undefined) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString(dateLocale.value)
}

const columns = computed<DataTableColumns<Letter>>(() => [
  { title: t('letter.professor'), key: 'professor_name', width: 168 },
  {
    title: t('letter.status'),
    key: 'is_generated',
    width: 138,
    render(row) {
      return row.is_generated
        ? h(NTag, { type: 'success', size: 'small' }, { default: () => t('letter.generated') })
        : h(NTag, { type: 'default', size: 'small' }, { default: () => t('letter.notGenerated') })
    },
  },
  {
    title: t('letter.generatedAt'),
    key: 'generated_at',
    width: 200,
    render(row) {
      return fmtDate(row.generated_at)
    },
  },
  {
    title: t('letter.preview'),
    key: 'content',
    ellipsis: { tooltip: true },
    render(row) {
      return row.content ? row.content.substring(0, 100) + '...' : '-'
    },
  },
  {
    title: t('letter.actions'),
    key: 'actions',
    width: 300,
    render(row) {
      return h(NSpace, { size: 'small', wrap: true }, () => [
        ...(row.is_generated
          ? [
              h(
                NButton,
                { size: 'small', onClick: () => showLetter(row) },
                { default: () => t('letter.viewEdit') }
              ),
            ]
          : []),
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            onClick: () => handleGenerate(row.professor_id),
          },
          { default: () => (row.is_generated ? t('match.regenerateLetter') : t('letter.generate')) }
        ),
      ])
    },
  },
])

async function fetchLetters() {
  loading.value = true
  try {
    data.value = await lettersApi.list({
      page: currentPage.value,
      page_size: data.value.page_size || 20,
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('letter.fetchListFailed'))
  } finally {
    loading.value = false
  }
}

function showLetter(letter: Letter) {
  currentLetter.value = letter
  editContent.value = letter.content || ''
  showLetterModal.value = true
}

function professorFallback(id: number) {
  return t('letter.fallBackProfessorNamed', { id })
}

async function handleGenerate(professorId: number) {
  try {
    const { task_id } = await lettersApi.generate(professorId, letterLanguage.value)
    const row = data.value.items.find((r) => r.professor_id === professorId)
    const name = row?.professor_name ?? professorFallback(professorId)
    taskStore.addTask(task_id, 'single-letter', t('professor.genLetterTask', { name }), 1, () => {
      fetchLetters()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('letter.generateFailed'))
  }
}

async function handleSave() {
  if (!currentLetter.value) return

  saving.value = true
  try {
    await lettersApi.update(currentLetter.value.professor_id, editContent.value)
    message.success(t('letter.saveSuccess'))
    showLetterModal.value = false
    fetchLetters()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('letter.saveFailed'))
  } finally {
    saving.value = false
  }
}

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(editContent.value)
    message.success(t('letter.copySuccess'))
  } catch {
    message.error(t('letter.copyFailed'))
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchLetters()
}

onMounted(() => {
  fetchLetters()
})
</script>

<template>
  <div>
    <n-card :title="$t('letter.title')">
      <n-space align="center" style="margin-bottom: 16px" wrap>
        <span>{{ $t('letter.letterLanguage') }}</span>
        <n-select
          v-model:value="letterLanguage"
          :options="letterLangOptions"
          style="width: 140px"
        />
      </n-space>
      <n-data-table
        :columns="columns"
        :data="data.items"
        :loading="loading"
        :row-key="(row: Letter) => row.professor_id"
        :scroll-x="1180"
      />

      <n-space justify="end" style="margin-top: 16px">
        <n-pagination
          :page="data.page"
          :page-count="data.pages"
          @update:page="handlePageChange"
        />
      </n-space>
    </n-card>

    <n-modal
      v-model:show="showLetterModal"
      preset="card"
      :title="currentLetter ? $t('letter.letterModalTitle', { name: currentLetter.professor_name }) : ''"
      style="width: 700px"
    >
      <n-input
        v-model:value="editContent"
        type="textarea"
        :rows="15"
        :placeholder="$t('letter.placeholderBody')"
      />

      <template #footer>
        <n-space justify="end">
          <n-button @click="handleCopy">{{ $t('letter.copyClipboard') }}</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">{{ $t('letter.saveChanges') }}</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>
