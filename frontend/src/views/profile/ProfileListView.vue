<script setup lang="ts">
import { ref, onMounted, h, shallowRef } from 'vue'
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
  NUpload,
  NSwitch,
  useMessage,
  useDialog,
} from 'naive-ui'
import type { DataTableColumns, UploadFileInfo } from 'naive-ui'
import { profilesApi } from '@/api/profiles'
import { useTaskStore } from '@/stores/tasks'
import type { Profile } from '@/types'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const taskStore = useTaskStore()

// State
const loading = ref(false)
const profiles = ref<Profile[]>([])
const selectedRowKeys = ref<number[]>([])

// Upload modal state
const showUploadModal = ref(false)
const uploadLoading = ref(false)
const uploadFiles = ref<UploadFileInfo[]>([])
const uploadRawFiles = shallowRef<File[]>([])
const uploadTitle = ref('')
const useLlm = ref(true)
const researchInterests = ref('')
const personalStatement = ref('')
const researchPlan = ref('')
const profileNotes = ref('')

// Table columns
const columns: DataTableColumns<Profile> = [
  {
    type: 'selection',
  },
  {
    title: '标题',
    key: 'title',
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '姓名',
    key: 'name',
    width: 120,
  },
  {
    title: '状态',
    key: 'is_active',
    width: 100,
    render(row) {
      return row.is_active
        ? h(NTag, { type: 'success', size: 'small' }, { default: () => '已激活' })
        : h(NTag, { type: 'default', size: 'small' }, { default: () => '未激活' })
    },
  },
  {
    title: '来源',
    key: 'source_format',
    width: 100,
    render(row) {
      return row.source_format === 'materials' ? '多材料' : row.source_format || '手动'
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 180,
    render(row) {
      return new Date(row.updated_at).toLocaleString('zh-CN')
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 250,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(
          NButton,
          {
            size: 'small',
            onClick: () => router.push(`/profile/${row.id}`),
          },
          { default: () => '查看' }
        ),
        !row.is_active &&
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              onClick: () => handleActivate(row.id),
            },
            { default: () => '激活' }
          ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete(row.id),
          },
          {
            trigger: () =>
              h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
            default: () => '确定删除该画像吗？',
          }
        ),
      ])
    },
  },
]

// Fetch profiles
async function fetchProfiles() {
  loading.value = true
  try {
    profiles.value = await profilesApi.list()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '获取画像列表失败')
  } finally {
    loading.value = false
  }
}

// Handle activate
async function handleActivate(id: number) {
  try {
    await profilesApi.activate(id)
    message.success('激活成功')
    await fetchProfiles()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '激活失败')
  }
}

// Handle delete
async function handleDelete(id: number) {
  try {
    await profilesApi.delete(id)
    message.success('删除成功')
    await fetchProfiles()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '删除失败')
  }
}

// Handle batch delete
async function handleBatchDelete() {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要删除的画像')
    return
  }

  dialog.warning({
    title: '确认删除',
    content: `确定删除选中的 ${selectedRowKeys.value.length} 份画像吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await profilesApi.batchDelete(selectedRowKeys.value)
        message.success('批量删除成功')
        selectedRowKeys.value = []
        await fetchProfiles()
      } catch (error: unknown) {
        const err = error as { response?: { data?: { detail?: string } } }
        message.error(err.response?.data?.detail || '批量删除失败')
      }
    },
  })
}

// Handle file upload
function handleFileChange(options: { file: UploadFileInfo; fileList: UploadFileInfo[] }) {
  uploadFiles.value = options.fileList
  uploadRawFiles.value = options.fileList
    .map((item) => item.file)
    .filter((candidate): candidate is File => candidate instanceof File)
}

async function handleUpload(): Promise<boolean> {
  const hasManualInput = [
    researchInterests.value,
    personalStatement.value,
    researchPlan.value,
    profileNotes.value,
  ].some((value) => value.trim())
  if (!uploadTitle.value) {
    message.warning('请输入标题')
    return false
  }
  if (uploadRawFiles.value.length === 0 && !hasManualInput) {
    message.warning('请至少上传一个材料文件或填写一项画像材料')
    return false
  }

  uploadLoading.value = true
  try {
    const result = await profilesApi.upload(
      uploadRawFiles.value,
      uploadTitle.value,
      {
        useLlm: useLlm.value,
        researchInterests: researchInterests.value,
        personalStatement: personalStatement.value,
        researchPlan: researchPlan.value,
        notes: profileNotes.value,
      }
    )
    taskStore.addTask(result.task_id, 'profile-generate', `生成学生画像 · ${uploadTitle.value}`, 3, () => {
      fetchProfiles()
    })
    message.success(result.message || '学生画像生成任务已加入任务列表')
    showUploadModal.value = false
    return false
  } catch (error: unknown) {
    const err = error as {
      code?: string
      message?: string
      response?: { status?: number; data?: { detail?: string } }
    }
    const detailValue = err.response?.data?.detail
    const detailText = Array.isArray(detailValue)
      ? detailValue
          .map((item) => (typeof item === 'object' && item ? item.msg || JSON.stringify(item) : String(item)))
          .join('; ')
      : detailValue

    const detail =
      detailText ||
      (err.code === 'ECONNABORTED' ? '请求超时（上传或解析耗时较长）' : '') ||
      err.message ||
      '上传生成失败'
    message.error(`上传生成失败：${detail}`)
    return false
  } finally {
    uploadLoading.value = false
  }
}

// Reset upload modal
function resetUploadModal() {
  uploadFiles.value = []
  uploadRawFiles.value = []
  uploadTitle.value = ''
  useLlm.value = true
  researchInterests.value = ''
  personalStatement.value = ''
  researchPlan.value = ''
  profileNotes.value = ''
}

onMounted(() => {
  fetchProfiles()
})
</script>

<template>
  <div>
    <n-card title="学生画像管理">
      <template #header-extra>
        <n-space>
          <n-button
            v-if="selectedRowKeys.length > 0"
            type="error"
            @click="handleBatchDelete"
          >
            批量删除 ({{ selectedRowKeys.length }})
          </n-button>
          <n-button type="primary" @click="showUploadModal = true">
            新建学生画像
          </n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="profiles"
        :loading="loading"
        :row-key="(row: Profile) => row.id"
        v-model:checked-row-keys="selectedRowKeys"
        :scroll-x="1000"
      />
    </n-card>

    <!-- Upload Modal -->
    <n-modal
      v-model:show="showUploadModal"
      preset="dialog"
      title="生成学生画像"
      positive-text="上传并生成"
      negative-text="取消"
      :positive-button-props="{ loading: uploadLoading }"
      @positive-click="handleUpload"
      @after-leave="resetUploadModal"
      style="width: 720px"
    >
      <n-form label-placement="top">
        <n-form-item label="标题">
          <n-input v-model:value="uploadTitle" placeholder="例如：NLP方向申请画像" />
        </n-form-item>
        <n-form-item label="材料文件">
          <n-upload
            multiple
            accept=".md,.markdown,.txt,.tex,.latex"
            :default-upload="false"
            :file-list="uploadFiles"
            @change="handleFileChange"
          >
            <n-button>选择文件 (.md/.markdown/.txt/.tex/.latex)</n-button>
          </n-upload>
        </n-form-item>
        <n-form-item label="研究兴趣">
          <n-input
            v-model:value="researchInterests"
            type="textarea"
            placeholder="例如：我对多模态大模型、医学图像理解和可解释性方向感兴趣"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="个人陈述">
          <n-input
            v-model:value="personalStatement"
            type="textarea"
            placeholder="可粘贴个人陈述或申请动机片段"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="研究计划">
          <n-input
            v-model:value="researchPlan"
            type="textarea"
            placeholder="可粘贴 research proposal / study plan 片段"
            :rows="3"
          />
        </n-form-item>
        <n-form-item label="补充备注">
          <n-input
            v-model:value="profileNotes"
            type="textarea"
            placeholder="其他希望画像优先参考的信息"
            :rows="2"
          />
        </n-form-item>
        <n-form-item label="提取背景字段">
          <n-switch v-model:value="useLlm" />
          <span style="margin-left: 8px; color: #999">
            用 LLM 从材料中辅助提取教育、经历、项目和技能
          </span>
        </n-form-item>
      </n-form>
    </n-modal>

  </div>
</template>
