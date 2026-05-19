<script setup lang="ts">
import { ref, onMounted, h, shallowRef, computed } from 'vue'
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
  NUpload,
  NSwitch,
  useMessage,
  useDialog,
} from 'naive-ui'
import type { DataTableColumns, UploadFileInfo } from 'naive-ui'
import { useDateLocale } from '@/composables/useDateLocale'
import { useApiError } from '@/composables/useApiError'
import { profilesApi } from '@/api/profiles'
import { useTaskStore } from '@/stores/tasks'
import type { Profile } from '@/types'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const taskStore = useTaskStore()
const { t, locale } = useI18n()
const { handleApiError } = useApiError()

const dateLocale = useDateLocale()

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

function sourceFormatLabel(format: string | undefined | null): string {
  if (format === 'materials') return t('profile.sourceMaterials')
  return format ? String(format) : t('profile.sourceManual')
}

// Table columns (reactive to locale)
const columns = computed<DataTableColumns<Profile>>(() => [
  {
    type: 'selection',
  },
  {
    title: t('profile.title'),
    key: 'title',
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: t('profile.name'),
    key: 'name',
    width: 140,
  },
  {
    title: t('profile.status'),
    key: 'is_active',
    width: 120,
    render(row) {
      return row.is_active
        ? h(NTag, { type: 'success', size: 'small' }, { default: () => t('profile.active') })
        : h(NTag, { type: 'default', size: 'small' }, { default: () => t('profile.inactive') })
    },
  },
  {
    title: t('profile.source'),
    key: 'source_format',
    width: 128,
    render(row) {
      return sourceFormatLabel(row.source_format)
    },
  },
  {
    title: t('profile.updatedAt'),
    key: 'updated_at',
    width: 200,
    render(row) {
      return new Date(row.updated_at).toLocaleString(dateLocale.value)
    },
  },
  {
    title: t('profile.actions'),
    key: 'actions',
    width: 368,
    render(row) {
      return h(NSpace, { size: 'small', wrap: true }, () => [
        h(
          NButton,
          {
            size: 'small',
            onClick: () => router.push(`/profile/${row.id}`),
          },
          { default: () => t('profile.view') }
        ),
        !row.is_active &&
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              onClick: () => handleActivate(row.id),
            },
            { default: () => t('profile.activate') }
          ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete(row.id),
          },
          {
            trigger: () =>
              h(NButton, { size: 'small', type: 'error' }, { default: () => t('profile.delete') }),
            default: () => t('profile.deleteConfirm'),
          }
        ),
      ])
    },
  },
])

// Fetch profiles
async function fetchProfiles() {
  loading.value = true
  try {
    profiles.value = await profilesApi.list()
  } catch (error: unknown) {
    handleApiError(error, t('profile.fetchListFailed'))
  } finally {
    loading.value = false
  }
}

// Handle activate
async function handleActivate(id: number) {
  try {
    await profilesApi.activate(id)
    message.success(t('profile.activateSuccess'))
    await fetchProfiles()
  } catch (error: unknown) {
    handleApiError(error, t('profile.activateFailed'))
  }
}

// Handle delete
async function handleDelete(id: number) {
  try {
    await profilesApi.delete(id)
    message.success(t('profile.deleteSuccess'))
    await fetchProfiles()
  } catch (error: unknown) {
    handleApiError(error, t('profile.deleteFailed'))
  }
}

// Handle batch delete
async function handleBatchDelete() {
  if (selectedRowKeys.value.length === 0) {
    message.warning(t('profile.pleaseSelectToDelete'))
    return
  }

  dialog.warning({
    title: t('profile.confirmDeleteTitle'),
    content: t('profile.batchDeleteConfirmCount', {
      count: selectedRowKeys.value.length,
    }),
    positiveText: t('common.confirm'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      try {
        await profilesApi.batchDelete(selectedRowKeys.value)
        message.success(t('profile.batchDeleteSuccess'))
        selectedRowKeys.value = []
        await fetchProfiles()
      } catch (error: unknown) {
        handleApiError(error, t('profile.batchDeleteFailed'))
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
    message.warning(t('profile.pleaseEnterTitle'))
    return false
  }
  if (uploadRawFiles.value.length === 0 && !hasManualInput) {
    message.warning(t('profile.needFileOrManual'))
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
    taskStore.addTask(result.task_id, 'profile-generate', t('task.profileGeneratingTask', { title: uploadTitle.value }), 3, () => {
      fetchProfiles()
    })
    message.success(result.message || t('profile.generateTaskQueued'))
    showUploadModal.value = false
    return false
  } catch (error: unknown) {
    const err = error as {
      code?: string
      message?: string
      response?: { status?: number; data?: { detail?: string | unknown[] } }
    }
    const detailValue = err.response?.data?.detail
    const detailText = Array.isArray(detailValue)
      ? detailValue
          .map((item) => (typeof item === 'object' && item ? (item as { msg?: string }).msg || JSON.stringify(item) : String(item)))
          .join('; ')
      : typeof detailValue === 'string'
        ? detailValue
        : ''

    const detail =
      detailText ||
      (err.code === 'ECONNABORTED' ? t('profile.timeoutHint') : '') ||
      err.message ||
      t('profile.generateFailed')
    message.error(t('profile.uploadGenerateFailed', { detail }))
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
    <n-card :title="$t('profile.management')">
      <template #header-extra>
        <n-space>
          <n-button
            v-if="selectedRowKeys.length > 0"
            type="error"
            @click="handleBatchDelete"
          >
            {{ $t('profile.batchDelete') }} ({{ selectedRowKeys.length }})
          </n-button>
          <n-button type="primary" @click="showUploadModal = true">
            {{ $t('profile.createNew') }}
          </n-button>
        </n-space>
      </template>

      <n-data-table
        :columns="columns"
        :data="profiles"
        :loading="loading"
        :row-key="(row: Profile) => row.id"
        v-model:checked-row-keys="selectedRowKeys"
        :scroll-x="1280"
      />
    </n-card>

    <!-- Upload Modal -->
    <n-modal
      v-model:show="showUploadModal"
      preset="dialog"
      :title="$t('profile.generateModalTitle')"
      :positive-text="$t('profile.uploadAndGenerate')"
      :negative-text="$t('common.cancel')"
      :positive-button-props="{ loading: uploadLoading }"
      @positive-click="handleUpload"
      @after-leave="resetUploadModal"
      style="width: 720px"
    >
      <n-form label-placement="top">
        <n-form-item :label="$t('profile.title')">
          <n-input v-model:value="uploadTitle" :placeholder="$t('profile.titleExamplePlaceholder')" />
        </n-form-item>
        <n-form-item :label="$t('profile.materialFilesLabel')">
          <n-upload
            multiple
            accept=".md,.markdown,.txt,.tex,.latex"
            :default-upload="false"
            :file-list="uploadFiles"
            @change="handleFileChange"
          >
            <n-button>{{ $t('profile.selectFilesButton') }}</n-button>
          </n-upload>
        </n-form-item>
        <n-form-item :label="$t('profile.researchInterests')">
          <n-input
            v-model:value="researchInterests"
            type="textarea"
            :placeholder="$t('profile.researchInterestsPlaceholder')"
            :rows="3"
          />
        </n-form-item>
        <n-form-item :label="$t('profile.personalStatement')">
          <n-input
            v-model:value="personalStatement"
            type="textarea"
            :placeholder="$t('profile.personalStatementPlaceholder')"
            :rows="3"
          />
        </n-form-item>
        <n-form-item :label="$t('profile.researchPlan')">
          <n-input
            v-model:value="researchPlan"
            type="textarea"
            :placeholder="$t('profile.researchPlanPlaceholder')"
            :rows="3"
          />
        </n-form-item>
        <n-form-item :label="$t('profile.freeNotes')">
          <n-input
            v-model:value="profileNotes"
            type="textarea"
            :placeholder="$t('profile.freeNotesPlaceholder')"
            :rows="2"
          />
        </n-form-item>
        <n-form-item :label="$t('profile.extractFieldsLabel')">
          <n-switch v-model:value="useLlm" />
          <span style="margin-left: 8px; color: var(--muted-foreground)">
            {{ $t('profile.extractFieldsHint') }}
          </span>
        </n-form-item>
      </n-form>
    </n-modal>

  </div>
</template>
