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
import type { Profile, ProfileCreate } from '@/types'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()

// State
const loading = ref(false)
const profiles = ref<Profile[]>([])
const selectedRowKeys = ref<number[]>([])

// Upload modal state
const showUploadModal = ref(false)
const uploadLoading = ref(false)
const uploadFile = ref<UploadFileInfo | null>(null)
const uploadRawFile = shallowRef<File | null>(null)
const uploadTitle = ref('')
const useLlm = ref(true)

// Parsed data for confirmation
const showConfirmModal = ref(false)
const parsedData = ref<ProfileCreate | null>(null)
const parseMessage = ref('')

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
            default: () => '确定删除该简历吗？',
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
    message.error(err.response?.data?.detail || '获取简历列表失败')
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
    message.warning('请选择要删除的简历')
    return
  }

  dialog.warning({
    title: '确认删除',
    content: `确定删除选中的 ${selectedRowKeys.value.length} 份简历吗？`,
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
  uploadFile.value = options.file
  const candidate = options.file?.file
  uploadRawFile.value = candidate instanceof File ? candidate : null
}

async function handleUpload(): Promise<boolean> {
  if (!uploadRawFile.value || !uploadTitle.value) {
    message.warning('请选择文件并输入标题')
    return false
  }

  uploadLoading.value = true
  try {
    const result = await profilesApi.upload(
      uploadRawFile.value,
      uploadTitle.value,
      useLlm.value
    )
    parsedData.value = result.parsed_data
    parseMessage.value = result.message
    showUploadModal.value = false
    showConfirmModal.value = true
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
      '上传解析失败'
    message.error(`上传解析失败：${detail}`)
    return false
  } finally {
    uploadLoading.value = false
  }
}

// Handle confirm save parsed profile
async function handleConfirmSave() {
  if (!parsedData.value) return

  try {
    await profilesApi.create(parsedData.value)
    message.success('保存成功')
    showConfirmModal.value = false
    parsedData.value = null
    await fetchProfiles()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '保存失败')
  }
}

// Reset upload modal
function resetUploadModal() {
  uploadFile.value = null
  uploadRawFile.value = null
  uploadTitle.value = ''
  useLlm.value = true
}

onMounted(() => {
  fetchProfiles()
})
</script>

<template>
  <div>
    <n-card title="简历管理">
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
            上传简历
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
      title="上传简历"
      positive-text="上传并解析"
      negative-text="取消"
      :positive-button-props="{ loading: uploadLoading }"
      @positive-click="handleUpload"
      @after-leave="resetUploadModal"
      style="width: 500px"
    >
      <n-form label-placement="left" label-width="80">
        <n-form-item label="标题">
          <n-input v-model:value="uploadTitle" placeholder="例如：NLP方向申请简历" />
        </n-form-item>
        <n-form-item label="文件">
          <n-upload
            :max="1"
            accept=".md,.tex"
            :default-upload="false"
            @change="handleFileChange"
          >
            <n-button>选择文件 (.md 或 .tex)</n-button>
          </n-upload>
        </n-form-item>
        <n-form-item label="使用 LLM">
          <n-switch v-model:value="useLlm" />
          <span style="margin-left: 8px; color: #999">
            使用 LLM 可提高解析准确度
          </span>
        </n-form-item>
      </n-form>
    </n-modal>

    <!-- Confirm Modal -->
    <n-modal
      v-model:show="showConfirmModal"
      preset="dialog"
      title="解析结果确认"
      positive-text="确认保存"
      negative-text="取消"
      @positive-click="handleConfirmSave"
      style="width: 600px"
    >
      <p style="color: #18a058">{{ parseMessage }}</p>
      <n-form v-if="parsedData" label-placement="top">
        <n-form-item label="姓名">
          <n-input v-model:value="parsedData.name" placeholder="姓名" />
        </n-form-item>
        <n-form-item label="技能">
          <n-input
            :value="parsedData.skills.join(', ')"
            @update:value="(v: string) => parsedData!.skills = v.split(',').map(s => s.trim()).filter(Boolean)"
            placeholder="用逗号分隔"
          />
        </n-form-item>
        <n-form-item label="教育经历">
          <div v-for="(edu, index) in parsedData.education" :key="index" style="margin-bottom: 8px">
            {{ edu.degree }} - {{ edu.school }} ({{ edu.period }})
          </div>
        </n-form-item>
        <n-form-item label="研究经历">
          <div v-for="(exp, index) in parsedData.research_experience" :key="index" style="margin-bottom: 8px">
            {{ exp.title }} @ {{ exp.organization }}
          </div>
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>
