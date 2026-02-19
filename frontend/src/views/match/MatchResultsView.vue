<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
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
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { matchApi } from '@/api/match'
import { lettersApi } from '@/api/letters'
import { useTaskStore } from '@/stores/tasks'
import type { MatchResult, MatchDetail, PaginatedResponse } from '@/types'

const message = useMessage()
const taskStore = useTaskStore()

// State
const loading = ref(false)
const data = ref<PaginatedResponse<MatchResult>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  pages: 1,
})
const currentPage = ref(1)

// Detail modal
const showDetailModal = ref(false)
const detailLoading = ref(false)
const matchDetail = ref<MatchDetail | null>(null)

// Generate letter loading state
const generatingLetter = ref<number | null>(null)

// Table columns
const columns: DataTableColumns<MatchResult> = [
  {
    title: '排名',
    key: 'rank',
    width: 70,
    render(_row, index) {
      return (currentPage.value - 1) * 20 + index + 1
    },
  },
  { title: '教授', key: 'professor_name', width: 150 },
  {
    title: '机构',
    key: 'professor_affiliation',
    ellipsis: { tooltip: true },
  },
  {
    title: '匹配度',
    key: 'score',
    width: 150,
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
    title: '匹配原因',
    key: 'match_reasons',
    width: 250,
    render(row) {
      return h(
        NSpace,
        { size: 'small' },
        () =>
          row.match_reasons.slice(0, 2).map((reason) =>
            h(NTag, { size: 'small' }, { default: () => reason })
          )
      )
    },
  },
  {
    title: '邮件状态',
    key: 'letter_generated',
    width: 100,
    render(row) {
      return row.letter_generated
        ? h(NTag, { type: 'success', size: 'small' }, { default: () => '已生成' })
        : h(NTag, { type: 'default', size: 'small' }, { default: () => '未生成' })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(
          NButton,
          { size: 'small', onClick: () => showMatchDetail(row.professor_id) },
          { default: () => '详情' }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            onClick: () => handleGenerateLetter(row.professor_id),
          },
          { default: () => (row.letter_generated ? '重新生成' : '生成邮件') }
        ),
      ])
    },
  },
]

// Fetch match results
async function fetchResults() {
  loading.value = true
  try {
    data.value = await matchApi.getResults({
      page: currentPage.value,
      page_size: 20,
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '获取匹配结果失败')
  } finally {
    loading.value = false
  }
}

// Run matching — now async task
async function handleRunMatch() {
  try {
    const { task_id, message: msg } = await matchApi.run()
    taskStore.addTask(task_id, 'match', '运行匹配算法', 0, () => {
      fetchResults()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '运行匹配失败')
  }
}

// Show match detail
async function showMatchDetail(professorId: number) {
  showDetailModal.value = true
  detailLoading.value = true
  try {
    matchDetail.value = await matchApi.getDetail(professorId)
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '获取详情失败')
    showDetailModal.value = false
  } finally {
    detailLoading.value = false
  }
}

// Generate letter — now async task
async function handleGenerateLetter(professorId: number) {
  try {
    const { task_id } = await lettersApi.generate(professorId)
    const row = data.value.items.find((r) => r.professor_id === professorId)
    const name = row?.professor_name ?? `教授 #${professorId}`
    taskStore.addTask(task_id, 'single-letter', `生成邮件 · ${name}`, 1, () => {
      fetchResults()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '生成邮件失败')
  }
}

// Handle page change
function handlePageChange(page: number) {
  currentPage.value = page
  fetchResults()
}

// Export to CSV
function handleExport() {
  const csv = [
    ['排名', '教授', '机构', '匹配度', '匹配原因', '邮件状态'].join(','),
    ...data.value.items.map((item, index) => [
      (currentPage.value - 1) * 20 + index + 1,
      item.professor_name,
      item.professor_affiliation || '',
      item.score,
      item.match_reasons.join('; '),
      item.letter_generated ? '已生成' : '未生成',
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
    <n-card title="匹配结果">
      <template #header-extra>
        <n-space>
          <n-button @click="handleExport" :disabled="data.items.length === 0">
            导出 CSV
          </n-button>
          <n-button type="primary" @click="handleRunMatch">
            运行匹配
          </n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="data.items"
        :loading="loading"
        :row-key="(row: MatchResult) => row.professor_id"
      />

      <n-space justify="end" style="margin-top: 16px">
        <n-pagination
          :page="data.page"
          :page-count="data.pages"
          @update:page="handlePageChange"
        />
      </n-space>
    </n-card>

    <!-- Match Detail Modal -->
    <n-modal
      v-model:show="showDetailModal"
      preset="card"
      :title="matchDetail?.professor_name || '匹配详情'"
      style="width: 600px"
    >
      <n-spin :show="detailLoading">
        <template v-if="matchDetail">
          <n-descriptions :column="1" label-placement="left" bordered>
            <n-descriptions-item label="机构">
              {{ matchDetail.professor_affiliation || '-' }}
            </n-descriptions-item>
            <n-descriptions-item label="匹配度">
              <n-progress
                type="line"
                :percentage="matchDetail.score"
                indicator-placement="inside"
              />
            </n-descriptions-item>
            <n-descriptions-item label="研究方向">
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
            <n-descriptions-item label="匹配原因">
              <div v-for="reason in matchDetail.match_reasons" :key="reason">
                • {{ reason }}
              </div>
            </n-descriptions-item>
          </n-descriptions>

          <div v-if="matchDetail.letter_content" style="margin-top: 16px">
            <h4>生成的邮件</h4>
            <pre style="white-space: pre-wrap; background: #f5f5f5; padding: 12px; border-radius: 4px">{{ matchDetail.letter_content }}</pre>
          </div>
        </template>
      </n-spin>
    </n-modal>
  </div>
</template>
