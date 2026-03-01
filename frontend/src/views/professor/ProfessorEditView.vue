<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton,
  NCard,
  NDynamicTags,
  NForm,
  NFormItem,
  NInput,
  NList,
  NListItem,
  NSpace,
  NTag,
  NThing,
  useMessage,
} from 'naive-ui'
import SourceInputPanel from '@/components/SourceInputPanel.vue'
import { professorsApi } from '@/api/professors'
import { sourceInputsApi } from '@/api/source-inputs'
import { useTaskStore } from '@/stores/tasks'
import type { PaperSummary, Professor, ProfessorEditPreviewResponse, SourceInput } from '@/types'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const taskStore = useTaskStore()

const loading = ref(false)
const previewing = ref(false)
const applying = ref(false)
const startingSummaryTask = ref(false)
const professor = ref<Professor | null>(null)
const sourceInputs = ref<SourceInput[]>([])
const preview = ref<ProfessorEditPreviewResponse | null>(null)

const form = ref({
  name: '',
  affiliation: '',
  email: '',
  homepage: '',
  research_interests: [] as string[],
  manual_notes: '',
})

const professorId = computed(() => Number(route.params.id))

async function fetchProfessor() {
  if (!professorId.value) {
    message.error('无效的教授 ID')
    router.push('/professor')
    return
  }
  loading.value = true
  try {
    const data = await professorsApi.get(professorId.value)
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
      sourceInputs.value = await sourceInputsApi.listByProfessor(professorId.value)
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

function buildManualPatch() {
  return {
    name: form.value.name || undefined,
    affiliation: form.value.affiliation || undefined,
    email: form.value.email || undefined,
    homepage: form.value.homepage || undefined,
    research_interests: form.value.research_interests,
    manual_notes: form.value.manual_notes || undefined,
  }
}

async function handlePreview() {
  if (!professorId.value) return
  previewing.value = true
  try {
    preview.value = await professorsApi.editPreview(professorId.value, {
      manual_patch: buildManualPatch(),
      source_input_ids: [],
    })
    message.success('已生成变更预览')
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '预览失败')
  } finally {
    previewing.value = false
  }
}

async function handleApply() {
  if (!professorId.value) return
  applying.value = true
  try {
    const updated = await professorsApi.applyEdits(professorId.value, {
      manual_patch: buildManualPatch(),
      source_input_ids: [],
    })
    professor.value = updated
    form.value = {
      name: updated.name,
      affiliation: updated.affiliation || '',
      email: updated.email || '',
      homepage: updated.homepage || '',
      research_interests: [...(updated.research_interests || [])],
      manual_notes: updated.manual_notes || '',
    }
    message.success('教授信息已更新')
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '应用变更失败')
  } finally {
    applying.value = false
  }
}

async function handleStartPaperSummary() {
  if (!professorId.value) return
  if (!sourceInputs.value.length) {
    message.warning('请先上传 PDF 或 ArXiv 来源')
    return
  }
  const summarizedSourceIds = new Set(
    summaryListFromProfessor()
      .map((item) => item.source_input_id)
      .filter((id): id is number => typeof id === 'number')
  )
  const sourceInputIds = sourceInputs.value
    .map((item) => item.id)
    .filter((id) => !summarizedSourceIds.has(id))
  if (!sourceInputIds.length) {
    message.info('当前来源均已总结，无需重复处理')
    return
  }

  startingSummaryTask.value = true
  try {
    const result = await professorsApi.startPaperSummary(professorId.value, sourceInputIds)
    taskStore.addTask(
      result.task_id,
      'paper-summary',
      '论文总结',
      sourceInputIds.length,
      () => {
        message.success('论文总结任务已完成')
        fetchProfessor()
      }
    )
    message.success('论文总结任务已加入任务列表，可先保存并离开当前页面')
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '启动论文总结任务失败')
  } finally {
    startingSummaryTask.value = false
  }
}

function summaryListFromProfessor() {
  return (professor.value?.paper_summaries || []) as PaperSummary[]
}

onMounted(fetchProfessor)
</script>

<template>
  <n-space vertical size="large">
    <n-card v-if="professor" :title="`编辑教授：${professor.name}`" :loading="loading">
      <template #header-extra>
        <n-space>
          <n-button @click="router.push('/professor')">返回列表</n-button>
          <n-button @click="fetchProfessor">刷新教授信息</n-button>
          <n-button type="info" :loading="previewing" @click="handlePreview">预览变更</n-button>
          <n-button type="primary" :loading="applying" @click="handleApply">确认保存</n-button>
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
          <n-input v-model:value="form.manual_notes" type="textarea" :rows="4" />
        </n-form-item>
      </n-form>
    </n-card>

    <SourceInputPanel v-model="sourceInputs">
      <template #actions>
        <n-button
          type="primary"
          secondary
          :loading="startingSummaryTask"
          @click="handleStartPaperSummary"
        >
          论文总结
        </n-button>
      </template>
    </SourceInputPanel>
    <div style="color: #888; font-size: 12px; margin-top: -8px">
      上传 PDF/ArXiv 后点击“论文总结”，后台完成后会自动保存到教师信息
    </div>

    <n-card v-if="preview" title="预览结果">
      <n-space vertical>
        <n-thing title="手动字段预览">
          <pre>{{ JSON.stringify(preview.manual_patch_applied, null, 2) }}</pre>
        </n-thing>
        <n-thing title="来源建议">
          <n-space vertical>
            <n-tag v-if="preview.source_suggestions.publications?.length" type="success">
              新增论文建议：{{ preview.source_suggestions.publications.length }} 条
            </n-tag>
            <n-tag v-if="preview.source_suggestions.paper_summaries?.length" type="info">
              新增论文总结：{{ preview.source_suggestions.paper_summaries.length }} 条
            </n-tag>
            <div
              v-if="
                !preview.source_suggestions.publications?.length &&
                !preview.source_suggestions.paper_summaries?.length
              "
            >
              暂无来源建议，当前仅应用手动编辑。
            </div>
          </n-space>
        </n-thing>
      </n-space>
    </n-card>

    <n-card title="论文总结列表（已保存）">
      <n-list bordered v-if="summaryListFromProfessor().length">
        <n-list-item
          v-for="(item, index) in summaryListFromProfessor()"
          :key="item.source_input_id || index"
        >
          <n-space vertical style="width: 100%">
            <div style="font-weight: 600">{{ item.title }}</div>
            <div style="color: #666">{{ item.summary || '-' }}</div>
            <n-space size="small" v-if="item.keywords?.length">
              <n-tag v-for="kw in item.keywords" :key="kw" type="warning" size="small">{{ kw }}</n-tag>
            </n-space>
          </n-space>
        </n-list-item>
      </n-list>
      <div v-else>暂无已保存的论文总结</div>
    </n-card>

  </n-space>
</template>
