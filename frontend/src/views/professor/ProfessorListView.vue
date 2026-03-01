<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
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
  NDrawer,
  NDrawerContent,
  NDescriptions,
  NDescriptionsItem,
  NList,
  NListItem,
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
import type { ProfessorListItem, Professor, PaginatedResponse } from '@/types'

const message = useMessage()
const dialog = useDialog()
const taskStore = useTaskStore()
const router = useRouter()

// State
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

// Add by Scholar modal
const showScholarModal = ref(false)
const scholarLoading = ref(false)
const scholarUrl = ref('')

// University crawl modal
const showUniversityModal = ref(false)
const universityLoading = ref(false)
const universityCrawlers = ref<UniversityCrawlerInfo[]>([])
const selectedUniversityId = ref<string>('')
const crawlersLoading = ref(false)

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
      message.error(err.response?.data?.detail || '获取院校列表失败')
    } finally {
      crawlersLoading.value = false
    }
  }
}

async function handleCrawlUniversity() {
  if (!selectedUniversityId.value) {
    message.warning('请选择目标院校')
    return
  }
  universityLoading.value = true
  try {
    const { task_id, message: msg } = await professorsApi.crawlUniversity(selectedUniversityId.value)
    showUniversityModal.value = false
    message.success(msg || '爬取任务已启动')
    taskStore.addTask(task_id, 'university-crawl', '院校批量导入', 0, () => {
      fetchProfessors()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '启动任务失败')
  } finally {
    universityLoading.value = false
  }
}

// Add manually modal
const showManualModal = ref(false)
const manualLoading = ref(false)
const manualForm = ref({
  name: '',
  affiliation: '',
  email: '',
  homepage: '',
  research_interests: [] as string[],
})

// Professor detail drawer
const showDetailDrawer = ref(false)
const detailLoading = ref(false)
const professorDetail = ref<Professor | null>(null)

// Table columns
const columns: DataTableColumns<ProfessorListItem> = [
  { type: 'selection' },
  { title: '姓名', key: 'name', width: 150 },
  {
    title: '机构',
    key: 'affiliation',
    ellipsis: { tooltip: true },
  },
  {
    title: '研究方向',
    key: 'research_interests',
    width: 250,
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
  { title: 'H-Index', key: 'h_index', width: 90 },
  {
    title: '操作',
    key: 'actions',
    width: 260,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(
          NButton,
          { size: 'small', type: 'primary', onClick: () => router.push(`/professor/${row.id}/edit`) },
          { default: () => '编辑' }
        ),
        h(
          NButton,
          { size: 'small', onClick: () => showDetail(row.id) },
          { default: () => '查看' }
        ),
        h(
          NButton,
          { size: 'small', type: 'info', onClick: () => handleRefresh(row.id) },
          { default: () => '更新' }
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row.id) },
          {
            trigger: () =>
              h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
            default: () => '确定删除该教授吗？',
          }
        ),
      ])
    },
  },
]

// Fetch professors
async function fetchProfessors() {
  loading.value = true
  try {
    data.value = await professorsApi.list({
      page: currentPage.value,
      page_size: 20,
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '获取教授列表失败')
  } finally {
    loading.value = false
  }
}

// Handle page change
function handlePageChange(page: number) {
  currentPage.value = page
  fetchProfessors()
}

// Add by Scholar URL — now async task
async function handleAddByScholar() {
  if (!scholarUrl.value) {
    message.warning('请输入 Google Scholar URL')
    return
  }

  scholarLoading.value = true
  try {
    const { task_id } = await professorsApi.addByScholar(scholarUrl.value)
    showScholarModal.value = false
    scholarUrl.value = ''
    taskStore.addTask(task_id, 'single-crawl', '爬取教授', 1, () => {
      fetchProfessors()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '添加失败')
  } finally {
    scholarLoading.value = false
  }
}

// Add manually
async function handleAddManually() {
  if (!manualForm.value.name) {
    message.warning('请输入教授姓名')
    return
  }

  manualLoading.value = true
  try {
    await professorsApi.create(manualForm.value)
    message.success('添加成功')
    showManualModal.value = false
    manualForm.value = {
      name: '',
      affiliation: '',
      email: '',
      homepage: '',
      research_interests: [],
    }
    fetchProfessors()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '添加失败')
  } finally {
    manualLoading.value = false
  }
}

// Show professor detail
async function showDetail(id: number) {
  showDetailDrawer.value = true
  detailLoading.value = true
  try {
    professorDetail.value = await professorsApi.get(id)
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '获取详情失败')
    showDetailDrawer.value = false
  } finally {
    detailLoading.value = false
  }
}

// Refresh professor data
async function handleRefresh(id: number) {
  try {
    await professorsApi.refresh(id)
    message.success('更新成功')
    fetchProfessors()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '更新失败')
  }
}

// Delete professor
async function handleDelete(id: number) {
  try {
    await professorsApi.delete(id)
    message.success('删除成功')
    fetchProfessors()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '删除失败')
  }
}

// Batch delete
async function handleBatchDelete() {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要删除的教授')
    return
  }

  dialog.warning({
    title: '确认删除',
    content: `确定删除选中的 ${selectedRowKeys.value.length} 位教授吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await professorsApi.batchDelete(selectedRowKeys.value)
        message.success('批量删除成功')
        selectedRowKeys.value = []
        fetchProfessors()
      } catch (error: unknown) {
        const err = error as { response?: { data?: { detail?: string } } }
        message.error(err.response?.data?.detail || '批量删除失败')
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
    <n-card title="教授管理">
      <template #header-extra>
        <n-space>
          <n-button
            v-if="selectedRowKeys.length > 0"
            type="error"
            @click="handleBatchDelete"
          >
            批量删除 ({{ selectedRowKeys.length }})
          </n-button>
          <n-button type="success" @click="openUniversityModal">
            院校官网批量添加
          </n-button>
          <n-button type="primary" @click="showScholarModal = true">
            Scholar 链接添加
          </n-button>
          <n-button @click="showManualModal = true">手动添加</n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="data.items"
        :loading="loading"
        :row-key="(row: ProfessorListItem) => row.id"
        v-model:checked-row-keys="selectedRowKeys"
        :scroll-x="960"
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

    <!-- University Crawl Modal -->
    <n-modal
      v-model:show="showUniversityModal"
      preset="dialog"
      title="院校官网批量添加"
      positive-text="开始爬取"
      negative-text="取消"
      :positive-button-props="{ loading: universityLoading, disabled: !selectedUniversityId }"
      @positive-click="handleCrawlUniversity"
      style="width: 480px"
    >
      <div style="padding: 8px 0">
        <p style="color: #666; margin-bottom: 16px; font-size: 13px">
          选择目标院校，系统将自动爬取该院系教授列表并导入。爬取过程在后台运行，可通过右下角任务面板查看进度。
        </p>
        <n-spin :show="crawlersLoading">
          <div v-if="!crawlersLoading && universityCrawlers.length === 0">
            <n-empty description="暂无可用的院校爬虫" />
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

    <!-- Add by Scholar Modal -->
    <n-modal
      v-model:show="showScholarModal"
      preset="dialog"
      title="通过 Google Scholar 添加"
      positive-text="添加"
      negative-text="取消"
      :positive-button-props="{ loading: scholarLoading }"
      @positive-click="handleAddByScholar"
      style="width: 500px"
    >
      <n-form-item label="Google Scholar URL">
        <n-input
          v-model:value="scholarUrl"
          placeholder="https://scholar.google.com/citations?user=xxx"
        />
      </n-form-item>
    </n-modal>

    <!-- Add Manually Modal -->
    <n-modal
      v-model:show="showManualModal"
      preset="dialog"
      title="手动添加教授"
      positive-text="添加"
      negative-text="取消"
      :positive-button-props="{ loading: manualLoading }"
      @positive-click="handleAddManually"
      style="width: 500px"
    >
      <n-form label-placement="left" label-width="80">
        <n-form-item label="姓名" required>
          <n-input v-model:value="manualForm.name" placeholder="教授姓名" />
        </n-form-item>
        <n-form-item label="机构">
          <n-input v-model:value="manualForm.affiliation" placeholder="所属大学/院系" />
        </n-form-item>
        <n-form-item label="邮箱">
          <n-input v-model:value="manualForm.email" placeholder="邮箱地址" />
        </n-form-item>
        <n-form-item label="主页">
          <n-input v-model:value="manualForm.homepage" placeholder="个人主页 URL" />
        </n-form-item>
        <n-form-item label="研究方向">
          <n-dynamic-tags v-model:value="manualForm.research_interests" />
        </n-form-item>
      </n-form>
    </n-modal>

    <!-- Professor Detail Drawer -->
    <n-drawer v-model:show="showDetailDrawer" :width="500">
      <n-drawer-content v-if="professorDetail" :title="professorDetail.name" :native-scrollbar="false">
        <n-descriptions :column="1" label-placement="left" bordered>
          <n-descriptions-item label="机构">
            {{ professorDetail.affiliation || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="邮箱">
            {{ professorDetail.email || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="主页">
            <a v-if="professorDetail.homepage" :href="professorDetail.homepage" target="_blank">
              {{ professorDetail.homepage }}
            </a>
            <span v-else>-</span>
          </n-descriptions-item>
          <n-descriptions-item label="H-Index">
            {{ professorDetail.h_index || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="总引用">
            {{ professorDetail.total_citations || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="研究方向">
            <n-space size="small">
              <n-tag
                v-for="interest in professorDetail.research_interests"
                :key="interest"
                type="info"
                size="small"
              >
                {{ interest }}
              </n-tag>
            </n-space>
          </n-descriptions-item>
        </n-descriptions>

        <h4 style="margin-top: 24px">论文列表</h4>
        <n-list bordered>
          <n-list-item v-for="(pub, index) in professorDetail.publications" :key="index">
            <div>
              <div style="font-weight: 500">{{ pub.title }}</div>
              <div style="color: #999; font-size: 12px">
                {{ pub.year || '-' }} · 引用: {{ pub.citations || 0 }}
              </div>
            </div>
          </n-list-item>
        </n-list>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>
