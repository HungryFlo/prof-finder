<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { useI18n } from 'vue-i18n'
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
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { matchApi } from '@/api/match'
import { lettersApi } from '@/api/letters'
import { useTaskStore } from '@/stores/tasks'
import type { MatchResult, MatchDetail, PaginatedResponse } from '@/types'

const message = useMessage()
const taskStore = useTaskStore()
const { t } = useI18n()

const loading = ref(false)
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

const letterLanguage = ref<'zh' | 'en'>('zh')
const letterLangOptions = computed(() => [
  { label: '中文', value: 'zh' as const },
  { label: 'English', value: 'en' as const },
])

const columns = computed<DataTableColumns<MatchResult>>(() => [
  {
    title: t('match.rank'),
    key: 'rank',
    width: 70,
    render(_row, index) {
      return (currentPage.value - 1) * data.value.page_size + index + 1
    },
  },
  { title: t('match.professor'), key: 'professor_name', width: 168 },
  {
    title: t('match.affiliation'),
    key: 'professor_affiliation',
    ellipsis: { tooltip: true },
  },
  {
    title: t('match.score'),
    key: 'score',
    width: 168,
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
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('match.fetchFailed'))
  } finally {
    loading.value = false
  }
}

async function handleRunMatch() {
  try {
    const { task_id } = await matchApi.run()
    taskStore.addTask(task_id, 'match', t('professor.runMatching'), 0, () => {
      fetchResults()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('match.runMatchFailed'))
  }
}

async function showMatchDetail(professorId: number) {
  showDetailModal.value = true
  detailLoading.value = true
  try {
    matchDetail.value = await matchApi.getDetail(professorId)
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('match.detailFetchFailed'))
    showDetailModal.value = false
  } finally {
    detailLoading.value = false
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
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('match.generateLetterFail'))
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

onMounted(() => {
  fetchResults()
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
          <n-button type="primary" @click="handleRunMatch">
            {{ $t('match.runMatch') }}
          </n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="data.items"
        :loading="loading"
        :row-key="(row: MatchResult) => row.professor_id"
        :scroll-x="1420"
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
      style="width: 620px"
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

          <div v-if="matchDetail.letter_content" style="margin-top: 16px">
            <h4>{{ $t('match.generatedLetterHeading') }}</h4>
            <pre style="white-space: pre-wrap; background: #f5f5f5; padding: 12px; border-radius: 4px">{{ matchDetail.letter_content }}</pre>
          </div>
        </template>
      </n-spin>
    </n-modal>
  </div>
</template>
