<script setup lang="ts">
import { ref, onMounted, h, computed, watch } from 'vue'
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
  NTabs,
  NTabPane,
  NAlert,
  NSwitch,
  NSelect,
  useMessage,
  useDialog,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { professorsApi } from '@/api/professors'
import { universitiesApi, type University } from '@/api/universities'
import { useApiError } from '@/composables/useApiError'
import type { UniversityCrawlerInfo, CrawlerTestResponse } from '@/api/professors'
import { useTaskStore } from '@/stores/tasks'
import ProfessorSummaryDrawer from '@/components/ProfessorSummaryDrawer.vue'
import type { ProfessorListItem, PaginatedResponse } from '@/types'

const message = useMessage()
const dialog = useDialog()
const { handleApiError } = useApiError()
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

const showDblpModal = ref(false)
const dblpLoading = ref(false)
const dblpUrl = ref('')

const showUniversityModal = ref(false)
const universityLoading = ref(false)
const universityCrawlers = ref<UniversityCrawlerInfo[]>([])
const selectedUniversityId = ref<string>('')
const crawlersLoading = ref(false)
const universityModalTab = ref<'builtin' | 'custom'>('builtin')

// Custom crawler form state
const customCrawlerForm = ref({
  name: '',
  university: '',
  department: '',
  list_url: '',
  extraction_mode: 'css' as 'css' | 'llm',
  affiliation: '',
  css_card: '',
  css_name: '',
  css_profile_url: '',
  css_title: '',
  css_email: '',
  css_research_interests: '',
  css_pagination_next: '',
  css_max_pages: '10',
})
const customCrawlerTesting = ref(false)
const customCrawlerSaving = ref(false)
const testResult = ref<CrawlerTestResponse | null>(null)

const showManualModal = ref(false)
const manualLoading = ref(false)
const manualForm = ref({
  name: '',
  affiliation: '',
  email: '',
  homepage: '',
  research_interests: [] as string[],
})

// University list for crawler config selector
const universityList = ref<University[]>([])
const selectedCrawlerUniversityId = ref<number | null>(null)

const showSummaryDrawer = ref(false)
const summaryDrawerProfId = ref(0)

const scholarMatchLoadingIds = ref<Set<number>>(new Set())
const externalMatchLoadingIds = ref<Set<number>>(new Set())

const searchQuery = ref('')
const sortBy = ref<string | null>(null)
const sortOrder = ref<'asc' | 'desc'>('desc')
const filterAffiliations = ref<string[]>([])
const affiliationOptions = ref<{ label: string; value: string }[]>([])

let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

watch(searchQuery, () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchProfessors()
  }, 300)
})

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
    sorter: 'default',
    render(row) {
      return h(
        'a',
        {
          style: 'cursor: pointer; color: var(--primary)',
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
    sorter: 'default',
    filter: 'default',
    filterOptions: affiliationOptions.value,
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
  { title: t('professor.hIndex'), key: 'h_index', width: 100, sorter: 'default' },
  {
    title: 'Scholar',
    key: 'enrichment_status',
    width: 110,
    render(row) {
      if (row.google_scholar_id) {
        return h(NTag, { size: 'small', type: 'success' }, { default: () => t('professor.scholarMatched') })
      }
      if (row.enrichment_status === 'pending') {
        return h(NTag, { size: 'small', type: 'info' }, { default: () => t('professor.scholarPending') })
      }
      if (row.enrichment_status === 'ambiguous') {
        return h(NTag, { size: 'small', type: 'warning' }, { default: () => t('professor.scholarAmbiguous') })
      }
      if (row.enrichment_status === 'not_found') {
        return h(NTag, { size: 'small', type: 'default' }, { default: () => t('professor.scholarNotFound') })
      }
      return null
    },
  },
  {
    title: 'DBLP',
    key: 'dblp_enrichment_status',
    width: 110,
    render(row) {
      if (row.dblp_pid) {
        return h(NTag, { size: 'small', type: 'success' }, { default: () => t('professor.dblpMatched') })
      }
      if (row.dblp_enrichment_status === 'pending') {
        return h(NTag, { size: 'small', type: 'info' }, { default: () => t('professor.dblpPending') })
      }
      if (row.dblp_enrichment_status === 'ambiguous') {
        return h(NTag, { size: 'small', type: 'warning' }, { default: () => t('professor.dblpAmbiguous') })
      }
      if (row.dblp_enrichment_status === 'not_found') {
        return h(NTag, { size: 'small', type: 'default' }, { default: () => t('professor.dblpNotFound') })
      }
      return null
    },
  },
  {
    title: t('professor.actions'),
    key: 'actions',
    width: 360,
    render(row) {
      const extLoading = externalMatchLoadingIds.value.has(row.id)
      const needsExternal = !row.google_scholar_id || !row.dblp_pid
      return h(NSpace, { size: 'small', wrap: true }, () => [
        h(
          NButton,
          { size: 'small', type: 'primary', onClick: () => router.push(`/professor/${row.id}`) },
          { default: () => t('professor.tableDetail') }
        ),
        needsExternal
          ? h(
              NButton,
              {
                size: 'small',
                type: 'info',
                secondary: true,
                loading: extLoading,
                disabled: extLoading,
                onClick: () => handleMatchExternal(row),
              },
              { default: () => t('professor.matchExternal') }
            )
          : null,
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
      const [crawlers, unis] = await Promise.all([
        professorsApi.getUniversityCrawlers(),
        universitiesApi.list().catch(() => []),
      ])
      universityCrawlers.value = crawlers
      universityList.value = unis
      if (universityCrawlers.value.length > 0) {
        const first = universityCrawlers.value[0]
        if (first) {
          selectedUniversityId.value = first.university_id
        }
      }
    } catch (error: unknown) {
      handleApiError(error, t('professor.fetchUniversityFailed'))
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
    handleApiError(error, t('professor.startTaskFailed'))
  } finally {
    universityLoading.value = false
  }
}

function buildCssSelectors() {
  const f = customCrawlerForm.value
  const selectors: Record<string, string | null> = {}
  if (f.css_card) selectors.card = f.css_card
  if (f.css_name) selectors.name = f.css_name
  if (f.css_profile_url) selectors.profile_url = f.css_profile_url
  if (f.css_title) selectors.title = f.css_title
  if (f.css_email) selectors.email = f.css_email
  if (f.css_research_interests) selectors.research_interests = f.css_research_interests
  if (f.css_pagination_next) selectors.pagination_next = f.css_pagination_next
  if (f.css_max_pages) selectors.max_pages = f.css_max_pages
  return selectors
}

async function handleTestCrawler() {
  const f = customCrawlerForm.value
  if (!f.list_url) {
    message.warning(t('professor.crawlerUrlRequired'))
    return
  }
  if (f.extraction_mode === 'css' && !f.css_name) {
    message.warning(t('professor.crawlerNameSelectorRequired'))
    return
  }

  customCrawlerTesting.value = true
  testResult.value = null
  try {
    testResult.value = await professorsApi.testCrawlerConfig({
      list_url: f.list_url,
      extraction_mode: f.extraction_mode,
      css_selectors: f.extraction_mode === 'css' ? buildCssSelectors() : undefined,
      affiliation: f.affiliation || f.university || undefined,
      name: f.name || undefined,
      university: f.university || undefined,
      department: f.department || undefined,
    })
    if (testResult.value.success) {
      message.success(t('professor.crawlerTestSuccess', { count: testResult.value.total_found }))
    } else {
      message.error(testResult.value.error_message || t('professor.crawlerTestFailed'))
    }
  } catch (error: unknown) {
    handleApiError(error, t('professor.crawlerTestFailed'))
  } finally {
    customCrawlerTesting.value = false
  }
}

async function handleSaveAndCrawl() {
  const f = customCrawlerForm.value
  if (!f.name || !f.university || !f.list_url) {
    message.warning(t('professor.crawlerRequiredFields'))
    return
  }

  customCrawlerSaving.value = true
  try {
    const config = await professorsApi.createCrawlerConfig({
      name: f.name,
      university: f.university,
      department: f.department || undefined,
      list_url: f.list_url,
      extraction_mode: f.extraction_mode,
      css_selectors: f.extraction_mode === 'css' ? buildCssSelectors() : undefined,
      affiliation: f.affiliation || f.university || undefined,
      university_id: selectedCrawlerUniversityId.value || undefined,
    })
    const { task_id, message: msg } = await professorsApi.crawlWithConfig(
      config.id,
      testResult.value?.cache_key || undefined,
    )
    showUniversityModal.value = false
    message.success(msg || t('professor.crawlTaskStarted'))
    taskStore.addTask(task_id, 'generic-university-crawl', t('professor.customCrawlTask'), 0, afterImportTasksComplete)
  } catch (error: unknown) {
    handleApiError(error, t('professor.startTaskFailed'))
  } finally {
    customCrawlerSaving.value = false
  }
}

async function fetchAffiliations() {
  try {
    const affiliations = await professorsApi.getAffiliations()
    affiliationOptions.value = affiliations.map((a) => ({ label: a, value: a }))
  } catch {
    // Silently fail - filter dropdown will just be empty
  }
}

async function fetchProfessors() {
  loading.value = true
  try {
    data.value = await professorsApi.list({
      page: currentPage.value,
      page_size: 20,
      search: searchQuery.value || undefined,
      sort_by: sortBy.value || undefined,
      sort_order: sortBy.value ? sortOrder.value : undefined,
      affiliation: filterAffiliations.value.length > 0 ? filterAffiliations.value.join(',') : undefined,
    })
  } catch (error: unknown) {
    handleApiError(error, t('professor.fetchListFailed'))
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
  fetchProfessors()
}

function handleFiltersChange(filterState: Record<string, (string | number)[] | string | number | null | undefined>) {
  const aff = filterState['affiliation']
  filterAffiliations.value = Array.isArray(aff) ? aff.map(String) : []
  currentPage.value = 1
  fetchProfessors()
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

  scholarLoading.value = true
  try {
    const { task_id } = await professorsApi.addByScholar(scholarUrl.value)
    showScholarModal.value = false
    scholarUrl.value = ''
    taskStore.addTask(task_id, 'single-crawl', t('professor.importProfessorTask'), 1, afterImportTasksComplete)
  } catch (error: unknown) {
    handleApiError(error, t('professor.addFailed'))
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
    handleApiError(error, t('professor.manualAddFail'))
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
    handleApiError(error, t('professor.batchRefreshFail'))
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
    handleApiError(error, t('professor.batchProfilesFail'))
  }
}

async function handleMatchExternal(row: ProfessorListItem) {
  if (externalMatchLoadingIds.value.has(row.id)) return

  const next = new Set(externalMatchLoadingIds.value)
  next.add(row.id)
  externalMatchLoadingIds.value = next

  try {
    const { task_id, message: msg } = await professorsApi.matchExternal(row.id)
    message.success(msg || t('professor.matchExternalStarted'))
    taskStore.addTask(
      task_id,
      'batch-dblp-match',
      t('professor.matchExternal') + `: ${row.name}`,
      2,
      afterImportTasksComplete,
    )
  } catch (error: unknown) {
    handleApiError(error, t('professor.matchExternalFailed'))
  } finally {
    const done = new Set(externalMatchLoadingIds.value)
    done.delete(row.id)
    externalMatchLoadingIds.value = done
  }
}

async function handleAddByDblp() {
  if (!dblpUrl.value) {
    message.warning(t('professor.enterDblpUrl'))
    return
  }
  dblpLoading.value = true
  try {
    const { task_id } = await professorsApi.addByDblp(dblpUrl.value)
    showDblpModal.value = false
    dblpUrl.value = ''
    taskStore.addTask(task_id, 'single-dblp-crawl', t('professor.importProfessorTask'), 1, afterImportTasksComplete)
  } catch (error: unknown) {
    handleApiError(error, t('professor.addFailed'))
  } finally {
    dblpLoading.value = false
  }
}

async function handleBatchRefreshExternal() {
  if (selectedRowKeys.value.length === 0) {
    message.warning(t('professor.pleaseSelectProfessorToRefresh'))
    return
  }
  try {
    const { task_id, message: msg } = await professorsApi.batchRefreshExternal(selectedRowKeys.value)
    taskStore.addTask(
      task_id,
      'batch-refresh-external',
      t('professor.batchRefreshExternal') + ` (${selectedRowKeys.value.length})`,
      selectedRowKeys.value.length,
      afterImportTasksComplete,
    )
    message.success(msg || t('professor.batchRefreshStarting'))
  } catch (error: unknown) {
    handleApiError(error, t('professor.batchRefreshFail'))
  }
}

async function handleDelete(id: number) {
  try {
    await professorsApi.delete(id)
    message.success(t('professor.deleteOk'))
    fetchProfessors()
  } catch (error: unknown) {
    handleApiError(error, t('professor.deleteFail'))
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
        handleApiError(error, t('professor.deleteFail'))
      }
    },
  })
}

onMounted(() => {
  fetchProfessors()
  fetchAffiliations()
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
            type="info"
            secondary
            @click="handleBatchRefreshExternal"
          >
            {{ $t('professor.batchRefreshExternal') }} ({{ selectedRowKeys.length }})
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
          <n-button type="primary" secondary @click="showDblpModal = true">
            {{ $t('professor.addByDblp') }}
          </n-button>
          <n-button @click="showManualModal = true">{{ $t('professor.manualAdd') }}</n-button>
        </n-space>
      </template>

      <n-input
        v-model:value="searchQuery"
        :placeholder="$t('professor.searchPlaceholder')"
        clearable
        style="margin-bottom: 12px"
      />

      <n-data-table
        remote
        :columns="columns"
        :data="data.items"
        :loading="loading"
        :row-key="(row: ProfessorListItem) => row.id"
        v-model:checked-row-keys="selectedRowKeys"
        :scroll-x="1260"
        :sort-by="sortBy"
        :sort-order="sortOrder === 'asc' ? 'ascend' : 'descend'"
        @update:sorter="handleSorterChange"
        @update:filters="handleFiltersChange"
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
      preset="card"
      :title="$t('professor.univModalTitle')"
      style="width: 640px"
      :bordered="false"
    >
      <n-tabs v-model:value="universityModalTab" type="line">
        <!-- Built-in crawlers tab -->
        <n-tab-pane :name="'builtin'" :tab="$t('professor.crawlerBuiltinTab')">
          <p style="color: var(--muted-foreground); margin-bottom: 16px; font-size: 13px">
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
          <div style="margin-top: 16px; text-align: right">
            <n-space>
              <n-button @click="showUniversityModal = false">{{ $t('common.cancel') }}</n-button>
              <n-button
                type="primary"
                :loading="universityLoading"
                :disabled="!selectedUniversityId"
                @click="handleCrawlUniversity"
              >
                {{ $t('professor.univModalPositive') }}
              </n-button>
            </n-space>
          </div>
        </n-tab-pane>

        <!-- Custom crawler tab -->
        <n-tab-pane :name="'custom'" :tab="$t('professor.crawlerCustomTab')">
          <n-form label-placement="top" :show-feedback="false">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px">
              <n-form-item :label="$t('professor.crawlerName')" required>
                <n-input
                  v-model:value="customCrawlerForm.name"
                  :placeholder="$t('professor.crawlerNamePlaceholder')"
                />
              </n-form-item>
              <n-form-item :label="$t('professor.crawlerUniversity')" required>
                <n-input
                  v-model:value="customCrawlerForm.university"
                  :placeholder="$t('professor.crawlerUniversityPlaceholder')"
                />
              </n-form-item>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px">
              <n-form-item :label="$t('professor.crawlerDepartment')">
                <n-input
                  v-model:value="customCrawlerForm.department"
                  :placeholder="$t('professor.crawlerDepartmentPlaceholder')"
                />
              </n-form-item>
              <n-form-item :label="$t('professor.crawlerAffiliation')">
                <n-input
                  v-model:value="customCrawlerForm.affiliation"
                  :placeholder="$t('professor.crawlerAffiliationPlaceholder')"
                />
              </n-form-item>
            </div>
            <n-form-item :label="$t('professor.crawlerUniversitySelect')">
              <n-select
                v-model:value="selectedCrawlerUniversityId"
                :placeholder="$t('professor.crawlerUniversitySelectDesc')"
                :options="universityList.map(u => ({ label: u.full_name, value: u.id }))"
                clearable
              />
            </n-form-item>
            <n-form-item :label="$t('professor.crawlerListUrl')" required>
              <n-input
                v-model:value="customCrawlerForm.list_url"
                placeholder="https://cs.example.edu/faculty"
              />
            </n-form-item>
            <n-form-item :label="$t('professor.crawlerExtractionMode')">
              <n-radio-group v-model:value="customCrawlerForm.extraction_mode">
                <n-space>
                  <n-radio value="css">{{ $t('professor.crawlerModeCss') }}</n-radio>
                  <n-radio value="llm">{{ $t('professor.crawlerModeLlm') }}</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>

            <!-- CSS Selector fields -->
            <template v-if="customCrawlerForm.extraction_mode === 'css'">
              <n-alert type="info" style="margin-bottom: 12px" :show-icon="false">
                {{ $t('professor.cssSelectorsHelp') }}
              </n-alert>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px">
                <n-form-item :label="$t('professor.cssCard')">
                  <n-input
                    v-model:value="customCrawlerForm.css_card"
                    placeholder="div.faculty-card"
                  />
                </n-form-item>
                <n-form-item :label="$t('professor.cssName')" required>
                  <n-input
                    v-model:value="customCrawlerForm.css_name"
                    placeholder="h3.name a"
                  />
                </n-form-item>
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px">
                <n-form-item :label="$t('professor.cssProfileUrl')">
                  <n-input
                    v-model:value="customCrawlerForm.css_profile_url"
                    placeholder="h3.name a"
                  />
                </n-form-item>
                <n-form-item :label="$t('professor.cssTitle')">
                  <n-input
                    v-model:value="customCrawlerForm.css_title"
                    placeholder="span.title"
                  />
                </n-form-item>
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px">
                <n-form-item :label="$t('professor.cssEmail')">
                  <n-input
                    v-model:value="customCrawlerForm.css_email"
                    placeholder='a[href^="mailto:"]'
                  />
                </n-form-item>
                <n-form-item :label="$t('professor.cssResearchInterests')">
                  <n-input
                    v-model:value="customCrawlerForm.css_research_interests"
                    placeholder="span.interests"
                  />
                </n-form-item>
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px">
                <n-form-item :label="$t('professor.cssPaginationNext')">
                  <n-input
                    v-model:value="customCrawlerForm.css_pagination_next"
                    placeholder="a.next-page"
                  />
                </n-form-item>
                <n-form-item :label="$t('professor.cssMaxPages')">
                  <n-input
                    v-model:value="customCrawlerForm.css_max_pages"
                    placeholder="10"
                  />
                </n-form-item>
              </div>
            </template>

            <!-- LLM mode hint -->
            <template v-else>
              <n-alert type="info" style="margin-bottom: 12px" :show-icon="false">
                {{ $t('professor.llmModeHelp') }}
              </n-alert>
            </template>
          </n-form>

          <!-- Test result preview -->
          <div v-if="testResult" style="margin-top: 12px">
            <n-alert
              :type="testResult.success ? 'success' : 'error'"
              :title="testResult.success
                ? $t('professor.crawlerTestSuccess', { count: testResult.total_found })
                : (testResult.error_message || $t('professor.crawlerTestFailed'))"
              style="margin-bottom: 8px"
            />
            <div v-if="testResult.success && testResult.sample_results.length > 0">
              <p style="font-size: 12px; color: var(--muted-foreground); margin-bottom: 4px">
                {{ $t('professor.crawlerTestSample') }}
              </p>
              <div
                v-for="(item, idx) in testResult.sample_results"
                :key="idx"
                style="padding: 4px 8px; background: var(--code-color); border-radius: 4px; margin-bottom: 4px; font-size: 13px"
              >
                <strong>{{ item.name }}</strong>
                <span v-if="item.affiliation" style="color: var(--muted-foreground)"> — {{ item.affiliation }}</span>
                <span v-if="item.email" style="color: var(--muted-foreground)"> · {{ item.email }}</span>
              </div>
            </div>
          </div>

          <div style="margin-top: 16px; text-align: right">
            <n-space>
              <n-button @click="showUniversityModal = false">{{ $t('common.cancel') }}</n-button>
              <n-button
                :loading="customCrawlerTesting"
                @click="handleTestCrawler"
              >
                {{ $t('professor.crawlerTest') }}
              </n-button>
              <n-button
                type="primary"
                :loading="customCrawlerSaving"
                @click="handleSaveAndCrawl"
              >
                {{ $t('professor.crawlerSaveAndCrawl') }}
              </n-button>
            </n-space>
          </div>
        </n-tab-pane>
      </n-tabs>
    </n-modal>

    <n-modal
      v-model:show="showDblpModal"
      preset="dialog"
      :title="$t('professor.dblpModalTitle')"
      :positive-text="$t('professor.addByScholarPos')"
      :negative-text="$t('common.cancel')"
      :positive-button-props="{ loading: dblpLoading }"
      @positive-click="handleAddByDblp"
      style="width: 500px"
    >
      <p style="margin: 0 0 12px; color: var(--muted-foreground); font-size: 13px; line-height: 1.5">
        {{ $t('professor.dblpModalIntro') }}
      </p>
      <n-form-item :label="$t('professor.dblpFormLabel')">
        <n-input
          v-model:value="dblpUrl"
          placeholder="https://dblp.org/pid/l/AuthorName.html"
        />
      </n-form-item>
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
      <p style="margin: 0 0 12px; color: var(--muted-foreground); font-size: 13px; line-height: 1.5">
        {{ $t('help.scholarModalIntro') }}
      </p>
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
      <p style="margin: 0 0 12px; color: var(--muted-foreground); font-size: 13px; line-height: 1.5">
        {{ $t('help.manualModalIntro') }}
      </p>
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
