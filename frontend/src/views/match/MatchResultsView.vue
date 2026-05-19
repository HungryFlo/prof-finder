<script setup lang="ts">
import { ref, onMounted, h, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  NCard,
  NSpace,
  NButton,
  NDataTable,
  NTag,
  NProgress,
  NPagination,
  NModal,
  NDescriptions,
  NDescriptionsItem,
  NSpin,
  NSelect,
  NInput,
  NDivider,
  NIcon,
  NAlert,
  useMessage,
  useDialog,
} from 'naive-ui'
import { CopyOutline } from '@vicons/ionicons5'
import type { DataTableColumns } from 'naive-ui'
import { matchApi } from '@/api/match'
import { lettersApi } from '@/api/letters'
import { useTaskStore } from '@/stores/tasks'
import { useApiError } from '@/composables/useApiError'
import type { MatchResult, MatchDetail, PaginatedResponse } from '@/types'

const message = useMessage()
const dialog = useDialog()
const taskStore = useTaskStore()
const { handleApiError } = useApiError()
const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const modelDownloadTask = computed(() =>
  taskStore.taskList.find((t) => t.taskType === 'download-model' && (t.status === 'running' || t.status === 'pending'))
)
const modelDownloading = computed(() => !!modelDownloadTask.value)
const modelDownloadProgress = computed(() => {
  const task = modelDownloadTask.value
  if (!task) return 0
  return Math.min(task.current, 100)
})

const loading = ref(false)
const modelReady = ref(false)
const data = ref<PaginatedResponse<MatchResult>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  pages: 1,
})
const currentPage = ref(1)

const showDetailModal = ref(false)
const detailLoading = ref(false)
const matchDetail = ref<MatchDetail | null>(null)

const letterContent = ref('')
const letterSaving = ref(false)
const letterLoading = ref(false)
const isEditingLetter = ref(false)

const letterLanguage = ref<'zh' | 'en'>('zh')
const letterLangOptions = computed(() => [
  { label: '中文', value: 'zh' as const },
  { label: 'English', value: 'en' as const },
])

const searchQuery = ref('')
const sortBy = ref<string | null>(null)
const sortOrder = ref<'asc' | 'desc'>('desc')

let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

watch(searchQuery, () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchResults()
  }, 300)
})

const columns = computed<DataTableColumns<MatchResult>>(() => [
  {
    title: t('match.rank'),
    key: 'rank',
    width: 70,
    render(_row, index) {
      return (currentPage.value - 1) * data.value.page_size + index + 1
    },
  },
  { title: t('match.professor'), key: 'professor_name', width: 168, sorter: 'default' },
  {
    title: t('match.affiliation'),
    key: 'professor_affiliation',
    ellipsis: { tooltip: true },
    sorter: 'default',
  },
  {
    title: t('match.score'),
    key: 'score',
    width: 168,
    sorter: 'default',
    render(row) {
      return h(NProgress, {
        type: 'line',
        percentage: row.score,
        indicatorPlacement: 'inside',
        status: row.score >= 70 ? 'success' : row.score >= 40 ? 'warning' : 'error',
      })
    },
  },
  {
    title: t('match.reasons'),
    key: 'match_reasons',
    width: 268,
    render(row) {
      return h(
        NSpace,
        { size: 'small', wrap: true },
        () =>
          row.match_reasons.slice(0, 2).map((reason) =>
            h(
              NTag,
              { size: 'small', title: reason },
              {
                default: () =>
                  h(
                    'span',
                    {
                      style: {
                        maxWidth: '200px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        display: 'block',
                      },
                    },
                    reason,
                  ),
              },
            ),
          ),
      )
    },
  },
  {
    title: t('match.letterStatus'),
    key: 'letter_generated',
    width: 148,
    render(row) {
      return row.letter_generated
        ? h(NTag, { type: 'success', size: 'small' }, { default: () => t('letter.generated') })
        : h(NTag, { type: 'default', size: 'small' }, { default: () => t('letter.notGenerated') })
    },
  },
  {
    title: t('match.actions'),
    key: 'actions',
    width: 320,
    render(row) {
      return h(NSpace, { size: 'small', wrap: true }, () => [
        h(
          NButton,
          { size: 'small', onClick: () => showMatchDetail(row.professor_id) },
          { default: () => t('match.detail') }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            onClick: () => handleGenerateLetter(row.professor_id),
          },
          { default: () => (row.letter_generated ? t('match.regenerateLetter') : t('match.generateLetter')) }
        ),
      ])
    },
  },
])

async function fetchResults() {
  loading.value = true
  try {
    data.value = await matchApi.getResults({
      page: currentPage.value,
      page_size: data.value.page_size || 20,
      search: searchQuery.value || undefined,
      sort_by: sortBy.value || undefined,
      sort_order: sortBy.value ? sortOrder.value : undefined,
    })
  } catch (error: unknown) {
    handleApiError(error, t('match.fetchFailed'))
  } finally {
    loading.value = false
  }
}

function handleSorterChange(sorter: { columnKey: string | number | null; order: 'ascend' | 'descend' | false }) {
  if (sorter.order === false) {
    sortBy.value = null
    sortOrder.value = 'desc'
  } else {
    sortBy.value = String(sorter.columnKey)
    sortOrder.value = sorter.order === 'ascend' ? 'asc' : 'desc'
  }
  currentPage.value = 1
  fetchResults()
}

async function checkModelStatus() {
  try {
    const { ready } = await matchApi.getModelStatus()
    modelReady.value = ready
  } catch {
    modelReady.value = false
  }
}

async function handleDownloadModel() {
  try {
    const { task_id } = await matchApi.downloadModel()
    taskStore.addTask(task_id, 'download-model', t('match.downloadingModel'), 1, () => {
      modelReady.value = true
    })
  } catch (error: unknown) {
    handleApiError(error, t('match.downloadModelFailed'))
  }
}

function promptDownloadModel() {
  dialog.warning({
    title: t('match.modelNotReadyTitle'),
    content: t('match.modelNotReadyDesc'),
    positiveText: t('match.downloadModel'),
    negativeText: t('common.cancel'),
    onPositiveClick: () => {
      handleDownloadModel()
    },
  })
}

async function handleRunMatch() {
  if (!modelReady.value) {
    promptDownloadModel()
    return
  }
  try {
    const { task_id } = await matchApi.run()
    taskStore.addTask(task_id, 'match', t('professor.runMatching'), 0, () => {
      fetchResults()
    })
  } catch (error: unknown) {
    // Backend returns MODEL_NOT_DOWNLOADED if model was removed after page load
    if ((error as any)?.response?.data?.detail === 'MODEL_NOT_DOWNLOADED') {
      modelReady.value = false
      promptDownloadModel()
      return
    }
    handleApiError(error, t('match.runMatchFailed'))
  }
}

async function showMatchDetail(professorId: number) {
  showDetailModal.value = true
  detailLoading.value = true
  letterContent.value = ''
  isEditingLetter.value = false
  try {
    matchDetail.value = await matchApi.getDetail(professorId)
    await loadLetterContent(professorId)
  } catch (error: unknown) {
    handleApiError(error, t('match.detailFetchFailed'))
    showDetailModal.value = false
  } finally {
    detailLoading.value = false
  }
}

async function loadLetterContent(professorId: number) {
  letterLoading.value = true
  try {
    const letter = await lettersApi.get(professorId)
    letterContent.value = letter.content || ''
  } catch {
    letterContent.value = ''
  } finally {
    letterLoading.value = false
  }
}

async function handleSaveLetter(professorId: number) {
  letterSaving.value = true
  try {
    await lettersApi.update(professorId, letterContent.value)
    message.success(t('letter.saveSuccess'))
    fetchResults()
  } catch (error: unknown) {
    handleApiError(error, t('letter.saveFailed'))
  } finally {
    letterSaving.value = false
  }
}

async function handleCopyLetter() {
  try {
    await navigator.clipboard.writeText(letterContent.value)
    message.success(t('letter.copySuccess'))
  } catch {
    message.error(t('letter.copyFailed'))
  }
}

async function handleGenerateFromModal(professorId: number) {
  try {
    const { task_id } = await lettersApi.generate(professorId, letterLanguage.value)
    const row = data.value.items.find((r) => r.professor_id === professorId)
    const name = row?.professor_name ?? professorFallbackName(professorId)
    taskStore.addTask(task_id, 'single-letter', t('professor.genLetterTask', { name }), 1, () => {
      fetchResults()
      loadLetterContent(professorId)
    })
  } catch (error: unknown) {
    handleApiError(error, t('match.generateLetterFail'))
  }
}

function professorFallbackName(id: number) {
  return t('professor.fallBackProfessorNamed', { id })
}

async function handleGenerateLetter(professorId: number) {
  try {
    const { task_id } = await lettersApi.generate(professorId, letterLanguage.value)
    const row = data.value.items.find((r) => r.professor_id === professorId)
    const name = row?.professor_name ?? professorFallbackName(professorId)
    taskStore.addTask(task_id, 'single-letter', t('professor.genLetterTask', { name }), 1, () => {
      fetchResults()
    })
  } catch (error: unknown) {
    handleApiError(error, t('match.generateLetterFail'))
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchResults()
}

function handleExport() {
  const csv = [
    [
      t('match.csvRank'),
      t('match.csvProfessor'),
      t('match.csvAffiliation'),
      t('match.csvScore'),
      t('match.csvReasons'),
      t('match.csvLetterStatus'),
    ].join(','),
    ...data.value.items.map((item, index) => [
      (currentPage.value - 1) * (data.value.page_size || 20) + index + 1,
      item.professor_name,
      item.professor_affiliation || '',
      item.score,
      item.match_reasons.join('; '),
      item.letter_generated ? t('letter.generated') : t('letter.notGenerated'),
    ].join(',')),
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = 'match_results.csv'
  link.click()
}

onMounted(async () => {
  checkModelStatus()
  await fetchResults()

  const professorParam = route.query.professor
  if (professorParam) {
    const professorId = Number(professorParam)
    if (!isNaN(professorId)) {
      showMatchDetail(professorId)
    }
  }
})

watch(showDetailModal, (val) => {
  if (!val) {
    // Clean up query param when modal closes
    const { professor, ...rest } = route.query
    if (professor) {
      router.replace({ query: rest })
    }
  }
})
</script>

<template>
  <div>
    <n-card :title="$t('match.title')">
      <template #header-extra>
        <n-space align="center" wrap>
          <span>{{ $t('letter.letterLanguage') }}</span>
          <n-select
            v-model:value="letterLanguage"
            :options="letterLangOptions"
            style="width: 130px"
          />
          <n-button @click="handleExport" :disabled="data.items.length === 0">
            {{ $t('match.exportCsv') }}
          </n-button>
          <n-button
            v-if="!modelReady"
            type="warning"
            :loading="modelDownloading"
            :disabled="modelDownloading"
            @click="handleDownloadModel"
          >
            {{ modelDownloading ? $t('match.downloadingModel') : $t('match.downloadModel') }}
          </n-button>
          <n-button type="primary" :disabled="!modelReady || modelDownloading" @click="handleRunMatch">
            {{ $t('match.runMatch') }}
          </n-button>
        </n-space>
      </template>

      <n-alert
        v-if="modelDownloading"
        type="info"
        :title="$t('match.downloadingModel')"
        style="margin-bottom: 12px"
      >
        <n-progress
          type="line"
          :percentage="modelDownloadProgress"
          :show-indicator="true"
          :status="modelDownloadProgress >= 100 ? 'success' : 'default'"
        />
        <div style="margin-top: 8px; font-size: 13px; color: var(--muted-foreground)">
          {{ $t('match.modelDownloadHint') }}
        </div>
      </n-alert>

      <n-alert
        v-else-if="!modelReady"
        type="warning"
        :title="$t('match.modelNotReadyTitle')"
        style="margin-bottom: 12px"
      >
        {{ $t('match.modelNotReadyDesc') }}
      </n-alert>

      <n-input
        v-model:value="searchQuery"
        :placeholder="$t('match.searchPlaceholder')"
        clearable
        style="margin-bottom: 12px"
      />

      <n-data-table
        remote
        :columns="columns"
        :data="data.items"
        :loading="loading"
        :row-key="(row: MatchResult) => row.professor_id"
        :scroll-x="1420"
        :sort-by="sortBy"
        :sort-order="sortOrder === 'asc' ? 'ascend' : 'descend'"
        @update:sorter="handleSorterChange"
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
      v-model:show="showDetailModal"
      preset="card"
      :title="matchDetail?.professor_name || $t('match.detailTitleFallback')"
      style="width: 900px"
    >
      <n-spin :show="detailLoading">
        <template v-if="matchDetail">
          <n-descriptions :column="1" label-placement="left" bordered>
            <n-descriptions-item :label="$t('match.affiliation')">
              {{ matchDetail.professor_affiliation || '-' }}
            </n-descriptions-item>
            <n-descriptions-item :label="$t('match.score')">
              <n-progress
                type="line"
                :percentage="matchDetail.score"
                indicator-placement="inside"
              />
            </n-descriptions-item>
            <n-descriptions-item :label="$t('professor.researchInterests')">
              <n-space size="small">
                <n-tag
                  v-for="interest in matchDetail.professor_interests"
                  :key="interest"
                  type="info"
                  size="small"
                >
                  {{ interest }}
                </n-tag>
              </n-space>
            </n-descriptions-item>
            <n-descriptions-item :label="$t('match.reasons')">
              <div v-for="reason in matchDetail.match_reasons" :key="reason">
                • {{ reason }}
              </div>
            </n-descriptions-item>
          </n-descriptions>

          <n-divider />

          <h4 style="margin: 0 0 12px">{{ $t('match.letterContent') }}</h4>

          <n-spin :show="letterLoading">
            <template v-if="letterContent">
              <n-input
                v-if="isEditingLetter"
                v-model:value="letterContent"
                type="textarea"
                :rows="15"
                :placeholder="$t('letter.placeholderBody')"
              />
              <div
                v-else
                style="white-space: pre-wrap; line-height: 1.7; font-size: 13px; padding: 8px 0"
              >
                {{ letterContent }}
              </div>
            </template>
            <template v-else-if="!letterLoading">
              <div style="text-align: center; padding: 24px 0; color: var(--muted-foreground)">
                {{ $t('match.noLetterYet') }}
              </div>
            </template>
          </n-spin>
        </template>
      </n-spin>

      <template #footer>
        <n-space justify="end">
          <template v-if="matchDetail">
            <template v-if="letterContent">
              <n-button @click="handleCopyLetter">
                <template #icon><n-icon><CopyOutline /></n-icon></template>
                {{ $t('match.copyLetter') }}
              </n-button>
              <template v-if="isEditingLetter">
                <n-button @click="isEditingLetter = false; loadLetterContent(matchDetail.professor_id)">
                  {{ $t('common.cancel') }}
                </n-button>
                <n-button type="primary" :loading="letterSaving" @click="async () => { await handleSaveLetter(matchDetail!.professor_id); isEditingLetter = false }">
                  {{ $t('match.saveLetter') }}
                </n-button>
              </template>
              <template v-else>
                <n-button type="primary" @click="isEditingLetter = true">
                  {{ $t('common.edit') }}
                </n-button>
                <n-button @click="handleGenerateFromModal(matchDetail.professor_id)">
                  {{ $t('match.regenerateLetter') }}
                </n-button>
              </template>
            </template>
            <template v-else>
              <n-button type="primary" @click="handleGenerateFromModal(matchDetail.professor_id)">
                {{ $t('match.generateLetter') }}
              </n-button>
            </template>
          </template>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>
