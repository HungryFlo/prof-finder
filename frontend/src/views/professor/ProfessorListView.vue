<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NCard,
  NSpace,
  NButton,
  NDataTable,
  NTag,
  NPopconfirm,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NPagination,
  NDynamicTags,
  NRadioGroup,
  NRadio,
  NSpin,
  NEmpty,
  useMessage,
  useDialog,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { professorsApi } from '@/api/professors'
import type { UniversityCrawlerInfo } from '@/api/professors'
import { useTaskStore } from '@/stores/tasks'
import ProfessorSummaryDrawer from '@/components/ProfessorSummaryDrawer.vue'
import type { ProfessorListItem, PaginatedResponse } from '@/types'

const message = useMessage()
const dialog = useDialog()
const taskStore = useTaskStore()
const router = useRouter()
const { t } = useI18n()

const loading = ref(false)
const data = ref<PaginatedResponse<ProfessorListItem>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  pages: 1,
})
const selectedRowKeys = ref<number[]>([])
const currentPage = ref(1)

const showScholarModal = ref(false)
const scholarLoading = ref(false)
const scholarUrl = ref('')

const showUniversityModal = ref(false)
const universityLoading = ref(false)
const universityCrawlers = ref<UniversityCrawlerInfo[]>([])
const selectedUniversityId = ref<string>('')
const crawlersLoading = ref(false)

const showManualModal = ref(false)
const manualLoading = ref(false)
const manualForm = ref({
  name: '',
  affiliation: '',
  email: '',
  homepage: '',
  research_interests: [] as string[],
})

const showSummaryDrawer = ref(false)
const summaryDrawerProfId = ref(0)

/** After crawl/refresh tasks finish, pick up chained tasks (e.g. professor-enrichment). */
function afterImportTasksComplete() {
  void fetchProfessors().then(() => taskStore.restoreFromServer())
}

function openSummaryDrawer(id: number) {
  summaryDrawerProfId.value = id
  showSummaryDrawer.value = true
}

const columns = computed<DataTableColumns<ProfessorListItem>>(() => [
  { type: 'selection' },
  {
    title: t('professor.name'),
    key: 'name',
    width: 150,
    render(row) {
      return h(
        'a',
        {
          style: 'cursor: pointer; color: #2080f0',
          onClick: () => openSummaryDrawer(row.id),
        },
        row.name
      )
    },
  },
  {
    title: t('professor.affiliation'),
    key: 'affiliation',
    ellipsis: { tooltip: true },
  },
  {
    title: t('professor.researchInterests'),
    key: 'research_interests',
    width: 280,
    render(row) {
      return h(
        NSpace,
        { size: 'small' },
        () =>
          row.research_interests.slice(0, 3).map((interest) =>
            h(NTag, { size: 'small', type: 'info' }, { default: () => interest })
          )
      )
    },
  },
  { title: t('professor.hIndex'), key: 'h_index', width: 100 },
  {
    title: t('professor.actions'),
    key: 'actions',
    width: 240,
    render(row) {
      return h(NSpace, { size: 'small', wrap: true }, () => [
        h(
          NButton,
          { size: 'small', type: 'primary', onClick: () => router.push(`/professor/${row.id}`) },
          { default: () => t('professor.tableDetail') }
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row.id) },
          {
            trigger: () =>
              h(NButton, { size: 'small', type: 'error' }, { default: () => t('professor.delete') }),
            default: () => t('professor.deleteConfirm'),
          }
        ),
      ])
    },
  },
])

async function openUniversityModal() {
  showUniversityModal.value = true
  if (universityCrawlers.value.length === 0) {
    crawlersLoading.value = true
    try {
      universityCrawlers.value = await professorsApi.getUniversityCrawlers()
      if (universityCrawlers.value.length > 0) {
        const first = universityCrawlers.value[0]
        if (first) {
          selectedUniversityId.value = first.university_id
        }
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      message.error(err.response?.data?.detail || t('professor.fetchUniversityFailed'))
    } finally {
      crawlersLoading.value = false
    }
  }
}

async function handleCrawlUniversity() {
  if (!selectedUniversityId.value) {
    message.warning(t('professor.selectUniversity'))
    return
  }
  universityLoading.value = true
  try {
    const { task_id, message: msg } = await professorsApi.crawlUniversity(selectedUniversityId.value)
    showUniversityModal.value = false
    message.success(msg || t('professor.crawlTaskStarted'))
    taskStore.addTask(task_id, 'university-crawl', t('professor.univImportTask'), 0, afterImportTasksComplete)
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('professor.startTaskFailed'))
  } finally {
    universityLoading.value = false
  }
}

async function fetchProfessors() {
  loading.value = true
  try {
    data.value = await professorsApi.list({
      page: currentPage.value,
      page_size: 20,
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('professor.fetchListFailed'))
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchProfessors()
}

async function handleAddByScholar() {
  if (!scholarUrl.value) {
    message.warning(t('professor.enterScholarUrl'))
    return
  }

  const _addScholarClientT0 = Date.now()
  // #region agent log
  fetch('http://127.0.0.1:7318/ingest/97692725-482b-4e9a-9a4d-aa05d366e8fd', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'a6cce7' },
    body: JSON.stringify({
      sessionId: 'a6cce7',
      hypothesisId: 'H1',
      location: 'ProfessorListView.vue:handleAddByScholar',
      message: 'client_add_scholar_start',
      data: {},
      timestamp: Date.now(),
    }),
  }).catch(() => {})
  // #endregion
  scholarLoading.value = true
  try {
    const { task_id } = await professorsApi.addByScholar(scholarUrl.value)
    // #region agent log
    fetch('http://127.0.0.1:7318/ingest/97692725-482b-4e9a-9a4d-aa05d366e8fd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'a6cce7' },
      body: JSON.stringify({
        sessionId: 'a6cce7',
        hypothesisId: 'H4',
        location: 'ProfessorListView.vue:handleAddByScholar',
        message: 'client_add_scholar_ok',
        data: { task_id, client_elapsed_ms: Date.now() - _addScholarClientT0 },
        timestamp: Date.now(),
      }),
    }).catch(() => {})
    // #endregion
    showScholarModal.value = false
    scholarUrl.value = ''
    taskStore.addTask(task_id, 'single-crawl', t('professor.importProfessorTask'), 1, afterImportTasksComplete)
  } catch (error: unknown) {
    const err = error as {
      code?: string
      message?: string
      response?: { status?: number; data?: { detail?: string } }
    }
    // #region agent log
    fetch('http://127.0.0.1:7318/ingest/97692725-482b-4e9a-9a4d-aa05d366e8fd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'a6cce7' },
      body: JSON.stringify({
        sessionId: 'a6cce7',
        hypothesisId: err.code === 'ECONNABORTED' ? 'H1' : err.response ? 'H3' : 'H2',
        location: 'ProfessorListView.vue:handleAddByScholar',
        message: 'client_add_scholar_err',
        data: {
          client_elapsed_ms: Date.now() - _addScholarClientT0,
          code: err.code,
          axiosMessage: err.message,
          httpStatus: err.response?.status,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {})
    // #endregion
    message.error(err.response?.data?.detail || t('professor.addFailed'))
  } finally {
    scholarLoading.value = false
  }
}

async function handleAddManually() {
  if (!manualForm.value.name) {
    message.warning(t('professor.manualNameRequired'))
    return
  }

  manualLoading.value = true
  try {
    const created = await professorsApi.create(manualForm.value)
    message.success(t('professor.manualAddOk'))
    showManualModal.value = false
    manualForm.value = {
      name: '',
      affiliation: '',
      email: '',
      homepage: '',
      research_interests: [],
    }
    await fetchProfessors()
    if (created.enrichment_task_id) {
      taskStore.addTask(
        created.enrichment_task_id,
        'professor-enrichment',
        t('professor.enrichmentTask'),
        created.enrichment_task_total ?? 0,
        () => fetchProfessors()
      )
    }
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('professor.manualAddFail'))
  } finally {
    manualLoading.value = false
  }
}

async function handleBatchRefresh() {
  if (selectedRowKeys.value.length === 0) {
    message.warning(t('professor.pleaseSelectProfessorToRefresh'))
    return
  }

  try {
    const { task_id, message: msg } = await professorsApi.batchRefresh(selectedRowKeys.value)
    taskStore.addTask(
      task_id,
      'batch-refresh',
      t('professor.batchRefreshTask', { count: selectedRowKeys.value.length }),
      selectedRowKeys.value.length,
      afterImportTasksComplete
    )
    message.success(msg || t('professor.batchRefreshStarting'))
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('professor.batchRefreshFail'))
  }
}

async function handleBatchGenerateProfiles() {
  if (selectedRowKeys.value.length === 0) {
    message.warning(t('professor.pleaseSelectProfileGen'))
    return
  }

  try {
    const { task_id, message: msg } = await professorsApi.batchGenerateProfiles(selectedRowKeys.value)
    taskStore.addTask(
      task_id,
      'batch-professor-profiles',
      t('professor.batchProfilesTask', { count: selectedRowKeys.value.length }),
      selectedRowKeys.value.length,
      () => {
        fetchProfessors()
      }
    )
    message.success(msg || t('professor.batchProfilesStarted'))
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('professor.batchProfilesFail'))
  }
}

async function handleDelete(id: number) {
  try {
    await professorsApi.delete(id)
    message.success(t('professor.deleteOk'))
    fetchProfessors()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('professor.deleteFail'))
  }
}

async function handleBatchDelete() {
  if (selectedRowKeys.value.length === 0) {
    message.warning(t('professor.pleaseSelectProfessorDelete'))
    return
  }

  dialog.warning({
    title: t('profile.confirmDeleteTitle'),
    content: t('professor.confirmBatchDeleteProfessor', {
      count: selectedRowKeys.value.length,
    }),
    positiveText: t('common.confirm'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      try {
        await professorsApi.batchDelete(selectedRowKeys.value)
        message.success(t('professor.batchDeleteProfessorOk'))
        selectedRowKeys.value = []
        fetchProfessors()
      } catch (error: unknown) {
        const err = error as { response?: { data?: { detail?: string } } }
        message.error(err.response?.data?.detail || t('professor.deleteFail'))
      }
    },
  })
}

onMounted(() => {
  fetchProfessors()
})
</script>

<template>
  <div>
    <n-card :title="$t('professor.management')">
      <template #header-extra>
        <n-space>
          <n-button
            v-if="selectedRowKeys.length > 0"
            type="error"
            @click="handleBatchDelete"
          >
            {{ $t('professor.batchDelete') }} ({{ selectedRowKeys.length }})
          </n-button>
          <n-button
            v-if="selectedRowKeys.length > 0"
            type="info"
            @click="handleBatchRefresh"
          >
            {{ $t('professor.batchUpdate') }} ({{ selectedRowKeys.length }})
          </n-button>
          <n-button
            v-if="selectedRowKeys.length > 0"
            type="warning"
            @click="handleBatchGenerateProfiles"
          >
            {{ $t('professor.batchGenerateProfiles') }} ({{ selectedRowKeys.length }})
          </n-button>
          <n-button type="success" @click="openUniversityModal">
            {{ $t('professor.batchAddUniversity') }}
          </n-button>
          <n-button type="primary" @click="showScholarModal = true">
            {{ $t('professor.addByScholar') }}
          </n-button>
          <n-button @click="showManualModal = true">{{ $t('professor.manualAdd') }}</n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="data.items"
        :loading="loading"
        :row-key="(row: ProfessorListItem) => row.id"
        v-model:checked-row-keys="selectedRowKeys"
        :scroll-x="1180"
      />

      <n-space justify="end" style="margin-top: 16px">
        <n-pagination
          :page="data.page"
          :page-count="data.pages"
          :page-size="data.page_size"
          show-size-picker
          :page-sizes="[10, 20, 50]"
          @update:page="handlePageChange"
        />
      </n-space>
    </n-card>

    <n-modal
      v-model:show="showUniversityModal"
      preset="dialog"
      :title="$t('professor.univModalTitle')"
      :positive-text="$t('professor.univModalPositive')"
      :negative-text="$t('common.cancel')"
      :positive-button-props="{ loading: universityLoading, disabled: !selectedUniversityId }"
      @positive-click="handleCrawlUniversity"
      style="width: 480px"
    >
      <div style="padding: 8px 0">
        <p style="color: #666; margin-bottom: 16px; font-size: 13px">
          {{ $t('professor.univModalIntro') }}
        </p>
        <n-spin :show="crawlersLoading">
          <div v-if="!crawlersLoading && universityCrawlers.length === 0">
            <n-empty :description="$t('professor.noUniversityCrawler')" />
          </div>
          <n-radio-group
            v-else
            v-model:value="selectedUniversityId"
            style="width: 100%"
          >
            <n-space vertical>
              <n-radio
                v-for="crawler in universityCrawlers"
                :key="crawler.university_id"
                :value="crawler.university_id"
              >
                {{ crawler.display_name }}
              </n-radio>
            </n-space>
          </n-radio-group>
        </n-spin>
      </div>
    </n-modal>

    <n-modal
      v-model:show="showScholarModal"
      preset="dialog"
      :title="$t('professor.scholarModalTitle')"
      :positive-text="$t('professor.addByScholarPos')"
      :negative-text="$t('common.cancel')"
      :positive-button-props="{ loading: scholarLoading }"
      @positive-click="handleAddByScholar"
      style="width: 500px"
    >
      <n-form-item :label="$t('professor.scholarFormLabel')">
        <n-input
          v-model:value="scholarUrl"
          placeholder="https://scholar.google.com/citations?user=xxx"
        />
      </n-form-item>
    </n-modal>

    <n-modal
      v-model:show="showManualModal"
      preset="dialog"
      :title="$t('professor.manualModalTitle')"
      :positive-text="$t('professor.addByScholarPos')"
      :negative-text="$t('common.cancel')"
      :positive-button-props="{ loading: manualLoading }"
      @positive-click="handleAddManually"
      style="width: 500px"
    >
      <n-form label-placement="left" label-width="80">
        <n-form-item :label="$t('professor.name')" required>
          <n-input v-model:value="manualForm.name" :placeholder="$t('professor.placeholderProfName')" />
        </n-form-item>
        <n-form-item :label="$t('professor.affiliation')">
          <n-input v-model:value="manualForm.affiliation" :placeholder="$t('professor.placeholderDept')" />
        </n-form-item>
        <n-form-item :label="$t('professor.email')">
          <n-input v-model:value="manualForm.email" :placeholder="$t('professor.placeholderEmailAddr')" />
        </n-form-item>
        <n-form-item :label="$t('professor.homepage')">
          <n-input v-model:value="manualForm.homepage" :placeholder="$t('professor.placeholderManualHomepage')" />
        </n-form-item>
        <n-form-item :label="$t('professor.researchInterests')">
          <n-dynamic-tags v-model:value="manualForm.research_interests" />
        </n-form-item>
      </n-form>
    </n-modal>

    <ProfessorSummaryDrawer
      v-model:show="showSummaryDrawer"
      :professor-id="summaryDrawerProfId"
    />
  </div>
</template>
