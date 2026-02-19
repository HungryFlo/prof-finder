<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import {
  NCard,
  NSpace,
  NButton,
  NDataTable,
  NTag,
  NModal,
  NInput,
  NPagination,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { lettersApi } from '@/api/letters'
import { useTaskStore } from '@/stores/tasks'
import type { Letter, PaginatedResponse } from '@/types'

const message = useMessage()
const taskStore = useTaskStore()

// State
const loading = ref(false)
const data = ref<PaginatedResponse<Letter>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  pages: 1,
})
const currentPage = ref(1)

// Letter detail/edit modal
const showLetterModal = ref(false)
const currentLetter = ref<Letter | null>(null)
const editContent = ref('')
const saving = ref(false)

// Generating letter state
const generatingLetter = ref<number | null>(null)

// Table columns
const columns: DataTableColumns<Letter> = [
  { title: '教授', key: 'professor_name', width: 150 },
  {
    title: '状态',
    key: 'is_generated',
    width: 100,
    render(row) {
      return row.is_generated
        ? h(NTag, { type: 'success', size: 'small' }, { default: () => '已生成' })
        : h(NTag, { type: 'default', size: 'small' }, { default: () => '未生成' })
    },
  },
  {
    title: '生成时间',
    key: 'generated_at',
    width: 180,
    render(row) {
      return row.generated_at ? new Date(row.generated_at).toLocaleString('zh-CN') : '-'
    },
  },
  {
    title: '内容预览',
    key: 'content',
    ellipsis: { tooltip: true },
    render(row) {
      return row.content ? row.content.substring(0, 100) + '...' : '-'
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        row.is_generated &&
          h(
            NButton,
            { size: 'small', onClick: () => showLetter(row) },
            { default: () => '查看/编辑' }
          ),
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            onClick: () => handleGenerate(row.professor_id),
          },
          { default: () => (row.is_generated ? '重新生成' : '生成') }
        ),
      ])
    },
  },
]

// Fetch letters
async function fetchLetters() {
  loading.value = true
  try {
    data.value = await lettersApi.list({
      page: currentPage.value,
      page_size: 20,
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '获取邮件列表失败')
  } finally {
    loading.value = false
  }
}

// Show letter detail
function showLetter(letter: Letter) {
  currentLetter.value = letter
  editContent.value = letter.content || ''
  showLetterModal.value = true
}

// Generate letter — now async task
async function handleGenerate(professorId: number) {
  try {
    const { task_id } = await lettersApi.generate(professorId)
    const row = data.value.items.find((r) => r.professor_id === professorId)
    const name = row?.professor_name ?? `教授 #${professorId}`
    taskStore.addTask(task_id, 'single-letter', `生成邮件 · ${name}`, 1, () => {
      fetchLetters()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '生成邮件失败')
  }
}

// Save edited letter
async function handleSave() {
  if (!currentLetter.value) return

  saving.value = true
  try {
    await lettersApi.update(currentLetter.value.professor_id, editContent.value)
    message.success('保存成功')
    showLetterModal.value = false
    fetchLetters()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// Copy to clipboard
async function handleCopy() {
  try {
    await navigator.clipboard.writeText(editContent.value)
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败')
  }
}

// Handle page change
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
    <n-card title="联络邮件">
      <n-data-table
        :columns="columns"
        :data="data.items"
        :loading="loading"
        :row-key="(row: Letter) => row.professor_id"
      />

      <n-space justify="end" style="margin-top: 16px">
        <n-pagination
          :page="data.page"
          :page-count="data.pages"
          @update:page="handlePageChange"
        />
      </n-space>
    </n-card>

    <!-- Letter Modal -->
    <n-modal
      v-model:show="showLetterModal"
      preset="card"
      :title="`给 ${currentLetter?.professor_name} 的邮件`"
      style="width: 700px"
    >
      <n-input
        v-model:value="editContent"
        type="textarea"
        :rows="15"
        placeholder="邮件内容"
      />

      <template #footer>
        <n-space justify="end">
          <n-button @click="handleCopy">复制到剪贴板</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">保存修改</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>
