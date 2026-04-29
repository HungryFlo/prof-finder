<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDynamicTags,
  NEllipsis,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NList,
  NListItem,
  NPopconfirm,
  NSpace,
  NSpin,
  NTag,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import SourceInputPanel from '@/components/SourceInputPanel.vue'
import { professorsApi } from '@/api/professors'
import { sourceInputsApi } from '@/api/source-inputs'
import { useTaskStore } from '@/stores/tasks'
import type { PaperSummary, Professor, Publication, SourceInput } from '@/types'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const taskStore = useTaskStore()

const professorId = Number(route.params.id)

const loading = ref(false)
const saving = ref(false)
const professor = ref<Professor | null>(null)
const sourceInputs = ref<SourceInput[]>([])

const form = ref({
  name: '',
  affiliation: '',
  email: '',
  homepage: '',
  research_interests: [] as string[],
  manual_notes: '',
})

// Task operation loading states
const refreshLoading = ref(false)
const fillPublicationsLoading = ref(false)
const summarizeLoading = ref(false)
const generateProfileLoading = ref(false)

// Computed data
const publications = computed<Publication[]>(() => {
  return (professor.value?.publications || []) as Publication[]
})

const paperSummaries = computed<PaperSummary[]>(() => {
  return (professor.value?.paper_summaries || []) as PaperSummary[]
})

// Cross-reference: publication title → matching paper_summary
const summaryByTitle = computed(() => {
  const map = new Map<string, PaperSummary>()
  for (const s of paperSummaries.value) {
    if (s.title) map.set(s.title.toLowerCase(), s)
  }
  return map
})

function hasMatchingSummary(pub: Publication): boolean {
  if (!pub.title) return false
  return summaryByTitle.value.has(pub.title.toLowerCase())
}

// Publications data table
const publicationColumns: DataTableColumns<Publication> = [
  {
    title: '标题',
    key: 'title',
    width: 400,
    render(row) {
      const children: any[] = []
      if (row.gscholar_url) {
        children.push(
          h('a', {
            href: row.gscholar_url,
            target: '_blank',
            style: 'text-decoration: none; color: inherit; font-weight: 500',
          }, row.title)
        )
      } else {
        children.push(
          h('span', { style: 'font-weight: 500' }, row.title)
        )
      }
      if (hasMatchingSummary(row)) {
        children.push(
          h(NTag, { size: 'tiny', type: 'success', style: 'margin-left: 6px' }, { default: () => '有总结' })
        )
      }
      return h('div', { style: 'display: flex; align-items: center' }, children)
    },
  },
  { title: '年份', key: 'year', width: 60 },
  { title: '引用', key: 'citations', width: 60 },
  {
    title: '期刊/会议',
    key: 'journal',
    width: 180,
    render(row) {
      return row.journal || row.conference || '-'
    },
  },
  {
    title: '摘要',
    key: 'abstract',
    width: 300,
    render(row) {
      if (!row.abstract) return h('span', { style: 'color: #999' }, '-')
      return h(NEllipsis, {
        lineClamp: 2,
        tooltip: { width: 480 },
        style: 'font-size: 12px; color: #666',
      }, { default: () => row.abstract || '' })
    },
  },
]

async function fetchData() {
  if (!professorId) {
    message.error('无效的教授 ID')
    router.push('/professor')
    return
  }
  loading.value = true
  try {
    const data = await professorsApi.get(professorId)
    professor.value = data
    form.value = {
      name: data.name,
      affiliation: data.affiliation || '',
      email: data.email || '',
      homepage: data.homepage || '',
      research_interests: [...(data.research_interests || [])],
      manual_notes: data.manual_notes || '',
    }
    try {
      sourceInputs.value = await sourceInputsApi.listByProfessor(professorId)
    } catch {
      // non-critical
    }
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '加载教授信息失败')
    router.push('/professor')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const updated = await professorsApi.update(professorId, {
      name: form.value.name,
      affiliation: form.value.affiliation || undefined,
      email: form.value.email || undefined,
      homepage: form.value.homepage || undefined,
      research_interests: form.value.research_interests,
      manual_notes: form.value.manual_notes || undefined,
    })
    professor.value = updated
    message.success('保存成功')
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleRefreshScholar() {
  refreshLoading.value = true
  try {
    const updated = await professorsApi.refresh(professorId)
    professor.value = updated
    message.success('Scholar 数据已更新')
    await fetchData()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || 'Scholar 更新失败')
  } finally {
    refreshLoading.value = false
  }
}

async function handleFillPublications() {
  if (!professor.value || !professorId) return

  fillPublicationsLoading.value = true
  try {
    const { task_id, total } = await professorsApi.startFillPublications(professorId)
    message.success('论文详情获取任务已启动')
    taskStore.addTask(task_id, 'fill-publications', `获取论文摘要 · ${professor.value.name}`, total ?? 0, () => {
      fetchData()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '启动任务失败')
  } finally {
    fillPublicationsLoading.value = false
  }
}

async function handleSummarizeSources() {
  if (!professor.value || !professorId) return

  const summarizedIds = new Set(
    paperSummaries.value
      .map((s) => s.source_input_id)
      .filter((id): id is number => typeof id === 'number')
  )
  const pendingIds = sourceInputs.value
    .map((s) => s.id)
    .filter((id) => !summarizedIds.has(id))

  if (!pendingIds.length) {
    message.info('所有来源均已总结')
    return
  }

  summarizeLoading.value = true
  try {
    const { task_id } = await professorsApi.startPaperSummary(professorId, pendingIds)
    message.success('论文总结任务已启动')
    taskStore.addTask(task_id, 'paper-summary', `论文总结 · ${professor.value.name}`, pendingIds.length, () => {
      fetchData()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '启动论文总结失败')
  } finally {
    summarizeLoading.value = false
  }
}

async function handleGenerateProfile() {
  if (!professor.value || !professorId) return

  generateProfileLoading.value = true
  try {
    const { task_id, message: msg } = await professorsApi.generateProfile(professorId)
    message.success(msg || '科研画像生成任务已启动')
    taskStore.addTask(task_id, 'professor-profile', `生成科研画像 · ${professor.value.name}`, 3, () => {
      fetchData()
    })
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '启动画像生成失败')
  } finally {
    generateProfileLoading.value = false
  }
}

function formatJsonNote(note: unknown): string {
  return typeof note === 'string' ? note : JSON.stringify(note)
}

onMounted(fetchData)
</script>

<template>
  <n-spin :show="loading">
    <n-space v-if="professor" vertical size="large">
      <!-- 1. Basic Info Card -->
      <n-card title="基本信息">
        <template #header-extra>
          <n-space>
            <n-button @click="router.push('/professor')">返回列表</n-button>
            <n-button type="primary" :loading="saving" @click="handleSave">
              保存
            </n-button>
          </n-space>
        </template>

        <n-form label-placement="top">
          <n-form-item label="姓名">
            <n-input v-model:value="form.name" />
          </n-form-item>
          <n-form-item label="机构">
            <n-input v-model:value="form.affiliation" />
          </n-form-item>
          <n-form-item label="邮箱">
            <n-input v-model:value="form.email" />
          </n-form-item>
          <n-form-item label="主页">
            <n-input v-model:value="form.homepage" />
          </n-form-item>
          <n-form-item label="研究方向">
            <n-dynamic-tags v-model:value="form.research_interests" />
          </n-form-item>
          <n-form-item label="手工备注">
            <n-input
              v-model:value="form.manual_notes"
              type="textarea"
              :rows="4"
              placeholder="可用于补充教授的研究方向、招生偏好等备注信息"
            />
          </n-form-item>
        </n-form>
      </n-card>

      <!-- 2. Source Inputs Card -->
      <SourceInputPanel v-model="sourceInputs">
        <template #actions>
          <n-button
            type="primary"
            secondary
            :loading="summarizeLoading"
            @click="handleSummarizeSources"
          >
            论文总结
          </n-button>
        </template>
      </SourceInputPanel>
      <div style="color: #888; font-size: 12px; margin-top: -8px">
        上传 PDF/ArXiv 后点击「论文总结」，后台完成后自动保存到教授信息
      </div>

      <!-- 3. Publications Card -->
      <n-card title="论文列表（Google Scholar）">
        <template #header-extra>
          <n-space>
            <n-popconfirm @positive-click="handleRefreshScholar">
              <template #trigger>
                <n-button size="small" :loading="refreshLoading">
                  Scholar 更新
                </n-button>
              </template>
              <template v-if="paperSummaries.length">
                Scholar 更新会清空已有的论文总结，确定继续？
              </template>
              <template v-else>
                确定从 Google Scholar 重新同步数据？
              </template>
            </n-popconfirm>
            <n-button
              size="small"
              type="info"
              :loading="fillPublicationsLoading"
              @click="handleFillPublications"
            >
              获取论文摘要
            </n-button>
          </n-space>
        </template>

        <n-data-table
          v-if="publications.length"
          :columns="publicationColumns"
          :data="publications"
          :row-key="(_row: Publication, index: number) => index"
          :max-height="500"
          size="small"
        />
        <n-empty v-else description="暂无论文数据" />
      </n-card>

      <!-- 4. Paper Summaries Card -->
      <n-card title="论文总结（来源输入）">
        <n-list v-if="paperSummaries.length" bordered>
          <n-list-item
            v-for="(item, index) in paperSummaries"
            :key="item.source_input_id || index"
          >
            <n-space vertical style="width: 100%">
              <div style="font-weight: 600">{{ item.title }}</div>
              <div style="color: #666; font-size: 13px">
                {{ item.summary || '-' }}
              </div>
              <n-space v-if="item.keywords?.length" size="small">
                <n-tag
                  v-for="kw in item.keywords"
                  :key="kw"
                  type="warning"
                  size="small"
                >
                  {{ kw }}
                </n-tag>
              </n-space>
              <n-tag
                v-if="item.source_type"
                size="tiny"
                :type="item.source_type === 'arxiv' ? 'info' : 'success'"
              >
                {{ item.source_type }}
              </n-tag>
            </n-space>
          </n-list-item>
        </n-list>
        <n-empty v-else description="暂无论文总结，上传 PDF/ArXiv 后点击「论文总结」生成" />
      </n-card>

      <!-- 5. Research Profile Card -->
      <n-card v-if="professor.research_profile" title="科研画像">
        <template #header-extra>
          <n-space>
            <n-tag v-if="professor.research_profile_generated_at" type="success">
              {{ new Date(professor.research_profile_generated_at).toLocaleString('zh-CN') }}
            </n-tag>
            <n-button
              size="small"
              :loading="generateProfileLoading"
              @click="handleGenerateProfile"
            >
              重新生成
            </n-button>
          </n-space>
        </template>
        <div
          style="
            white-space: pre-wrap;
            background: var(--n-color-modal);
            padding: 16px;
            border-radius: 6px;
            border: 1px solid var(--n-border-color);
            font-size: 13px;
            line-height: 1.7;
          "
        >
          {{ professor.research_profile }}
        </div>

        <n-space
          v-if="professor.research_profile_evidence?.length"
          vertical
          style="margin-top: 16px"
        >
          <strong>证据摘要</strong>
          <div>
            <n-tag
              v-for="(note, index) in professor.research_profile_evidence"
              :key="index"
              style="margin: 0 8px 8px 0"
            >
              {{ formatJsonNote(note) }}
            </n-tag>
          </div>
        </n-space>

        <n-space
          v-if="professor.research_profile_conflicts?.length"
          vertical
          style="margin-top: 16px"
        >
          <strong>冲突说明</strong>
          <div>
            <n-tag
              v-for="(note, index) in professor.research_profile_conflicts"
              :key="index"
              type="warning"
              style="margin: 0 8px 8px 0"
            >
              {{ formatJsonNote(note) }}
            </n-tag>
          </div>
        </n-space>
      </n-card>

      <n-card v-else title="科研画像">
        <n-empty description="尚未生成科研画像">
          <template #extra>
            <n-button
              type="warning"
              :loading="generateProfileLoading"
              @click="handleGenerateProfile"
            >
              生成科研画像
            </n-button>
          </template>
        </n-empty>
      </n-card>
    </n-space>

    <n-empty v-else-if="!loading" description="教授不存在" />
  </n-spin>
</template>
