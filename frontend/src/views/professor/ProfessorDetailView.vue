<script setup lang="ts">
import { computed, h, inject, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
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
  NDataTable,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import SourceInputPanel from '@/components/SourceInputPanel.vue'
import { professorsApi } from '@/api/professors'
import { sourceInputsApi } from '@/api/source-inputs'
import { useApiError } from '@/composables/useApiError'
import { useTaskStore } from '@/stores/tasks'
import { useDateLocale } from '@/composables/useDateLocale'
import type { PaperSummary, Professor, Publication, SourceInput } from '@/types'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const taskStore = useTaskStore()
const { handleApiError } = useApiError()
const { t } = useI18n()

const setBreadcrumbTitle = inject<(title: string) => void>('setBreadcrumbTitle', () => {})

const dateLocale = useDateLocale()

const professorId = Number(route.params.id)

const loading = ref(false)
const saving = ref(false)
const professor = ref<Professor | null>(null)
const sourceInputs = ref<SourceInput[]>([])

const form = ref({
  name: '',
  name_locales: { zh: '', en: '' },
  affiliation: '',
  email: '',
  homepage: '',
  research_interests: [] as string[],
  manual_notes: '',
})

const refreshLoading = ref(false)
const fillPublicationsLoading = ref(false)
const summarizeLoading = ref(false)
const generateProfileLoading = ref(false)

const publications = computed<Publication[]>(() => {
  return (professor.value?.publications || []) as Publication[]
})

const paperSummaries = computed<PaperSummary[]>(() => {
  return (professor.value?.paper_summaries || []) as PaperSummary[]
})

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

function fmtDate(iso: string | undefined | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString(dateLocale.value)
}

const publicationColumns = computed<DataTableColumns<Publication>>(() => [
  {
    title: t('professor.pubColTitle'),
    key: 'title',
    width: 420,
    render(row) {
      const children: ReturnType<typeof h>[] = []
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
          h(NTag, { size: 'tiny', type: 'success', style: 'margin-left: 6px' }, { default: () => t('professor.hasSummaryBadge') })
        )
      }
      return h('div', { style: 'display: flex; align-items: center' }, children)
    },
  },
  { title: t('professor.pubColYear'), key: 'year', width: 72 },
  { title: t('professor.pubColCitations'), key: 'citations', width: 88 },
  {
    title: t('professor.pubColVenue'),
    key: 'journal',
    width: 200,
    render(row) {
      return row.journal || row.conference || '-'
    },
  },
  {
    title: t('professor.pubColAbstract'),
    key: 'abstract',
    width: 340,
    render(row) {
      if (!row.abstract) return h('span', { style: 'color: var(--muted-foreground)' }, '-')
      return h(NEllipsis, {
        lineClamp: 2,
        tooltip: { width: 480 },
        style: 'font-size: 12px; color: var(--muted-foreground)',
      }, { default: () => row.abstract || '' })
    },
  },
])

async function fetchData() {
  if (!professorId) {
    message.error(t('professor.invalidId'))
    router.push('/professor')
    return
  }
  loading.value = true
  try {
    const data = await professorsApi.get(professorId)
    professor.value = data
    setBreadcrumbTitle(data.name)
    form.value = {
      name: data.name,
      name_locales: {
        zh: data.name_locales?.zh ?? '',
        en: data.name_locales?.en ?? '',
      },
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
    handleApiError(error, t('professor.loadFailed'))
    router.push('/professor')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const nl: Record<string, string> = {}
    const z = form.value.name_locales.zh?.trim()
    const e = form.value.name_locales.en?.trim()
    if (z) nl.zh = z
    if (e) nl.en = e
    const updated = await professorsApi.update(professorId, {
      name: form.value.name,
      name_locales: nl,
      affiliation: form.value.affiliation || undefined,
      email: form.value.email || undefined,
      homepage: form.value.homepage || undefined,
      research_interests: form.value.research_interests,
      manual_notes: form.value.manual_notes || undefined,
    })
    professor.value = updated
    message.success(t('profile.saveSuccess'))
  } catch (error: unknown) {
    handleApiError(error, t('profile.saveFailed'))
  } finally {
    saving.value = false
  }
}

async function handleRefreshScholar() {
  refreshLoading.value = true
  try {
    const updated = await professorsApi.refresh(professorId)
    professor.value = updated
    message.success(t('professor.scholarSynced'))
    await fetchData()
  } catch (error: unknown) {
    handleApiError(error, t('professor.scholarSyncFailed'))
  } finally {
    refreshLoading.value = false
  }
}

async function handleFillPublications() {
  if (!professor.value || !professorId) return

  fillPublicationsLoading.value = true
  try {
    const { task_id, total } = await professorsApi.startFillPublications(professorId)
    message.success(t('professor.abstractsTaskStarted'))
    taskStore.addTask(
      task_id,
      'fill-publications',
      t('professor.fetchAbstractsTask', { name: professor.value.name }),
      total ?? 0,
      () => {
        fetchData()
      }
    )
  } catch (error: unknown) {
    handleApiError(error, t('professor.startTaskFailed'))
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
    message.info(t('professor.summariesAllDone'))
    return
  }

  summarizeLoading.value = true
  try {
    const { task_id } = await professorsApi.startPaperSummary(professorId, pendingIds)
    message.success(t('professor.paperSummaryTaskStarted'))
    taskStore.addTask(
      task_id,
      'paper-summary',
      t('professor.summarizeTask', { name: professor.value.name }),
      pendingIds.length,
      () => {
        fetchData()
      }
    )
  } catch (error: unknown) {
    handleApiError(error, t('professor.paperSummaryStartFailed'))
  } finally {
    summarizeLoading.value = false
  }
}

async function handleGenerateProfile() {
  if (!professor.value || !professorId) return

  generateProfileLoading.value = true
  try {
    const { task_id, message: msg } = await professorsApi.generateProfile(professorId)
    message.success(msg || t('professor.generateProfileStarting'))
    taskStore.addTask(
      task_id,
      'professor-profile',
      t('professor.researchProfileGenTask', { name: professor.value.name }),
      3,
      () => {
        fetchData()
      }
    )
  } catch (error: unknown) {
    handleApiError(error, t('professor.generateProfileStartFailed'))
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
      <n-card :title="$t('professor.basicInfoCard')">
        <template #header-extra>
          <n-space>
            <n-button @click="router.push('/professor')">{{ $t('professor.backToList') }}</n-button>
            <n-button type="primary" :loading="saving" @click="handleSave">
              {{ $t('professor.save') }}
            </n-button>
          </n-space>
        </template>

        <n-form label-placement="top">
          <n-form-item :label="$t('professor.name')">
            <n-input v-model:value="form.name" />
          </n-form-item>
          <n-form-item :label="$t('professor.nameLocaleZh')">
            <n-input v-model:value="form.name_locales.zh" />
          </n-form-item>
          <n-form-item :label="$t('professor.nameLocaleEn')">
            <n-input v-model:value="form.name_locales.en" />
          </n-form-item>
          <n-form-item :label="$t('professor.affiliation')">
            <n-input v-model:value="form.affiliation" />
          </n-form-item>
          <n-form-item :label="$t('professor.email')">
            <n-input v-model:value="form.email" />
          </n-form-item>
          <n-form-item :label="$t('professor.homepage')">
            <n-input v-model:value="form.homepage" />
          </n-form-item>
          <n-form-item :label="$t('professor.researchInterests')">
            <n-dynamic-tags v-model:value="form.research_interests" />
          </n-form-item>
          <n-form-item :label="$t('professor.manualNotes')">
            <n-input
              v-model:value="form.manual_notes"
              type="textarea"
              :rows="4"
              :placeholder="$t('professor.manualNotesPlaceholder')"
            />
          </n-form-item>
        </n-form>
      </n-card>

      <SourceInputPanel v-model="sourceInputs">
        <template #actions>
          <n-button
            type="primary"
            secondary
            :loading="summarizeLoading"
            @click="handleSummarizeSources"
          >
            {{ $t('professor.summarizePapers') }}
          </n-button>
        </template>
      </SourceInputPanel>
      <div style="color: var(--muted-foreground); font-size: 12px; margin-top: -8px">
        {{ $t('professor.sourceCardsHintAfterUpload') }}
      </div>

      <n-card :title="$t('professor.publicationsCardTitle')">
        <template #header-extra>
          <n-space>
            <n-popconfirm @positive-click="handleRefreshScholar">
              <template #trigger>
                <n-button size="small" :loading="refreshLoading">
                  {{ $t('professor.scholarSyncButton') }}
                </n-button>
              </template>
              <template v-if="paperSummaries.length">
                {{ $t('professor.scholarSyncClearsSummaries') }}
              </template>
              <template v-else>
                {{ $t('professor.scholarResyncQuestion') }}
              </template>
            </n-popconfirm>
            <n-button
              size="small"
              type="info"
              :loading="fillPublicationsLoading"
              @click="handleFillPublications"
            >
              {{ $t('professor.fetchAbstracts') }}
            </n-button>
          </n-space>
        </template>

        <n-data-table
          v-if="publications.length"
          :columns="publicationColumns"
          :data="publications"
          :row-key="(row: Publication) => row.gscholar_url || `${row.title ?? ''}:${row.year ?? ''}:${row.citations ?? ''}`"
          :max-height="500"
          :scroll-x="1260"
          size="small"
        />
        <n-empty v-else :description="$t('professor.noPublications')" />
      </n-card>

      <n-card :title="$t('professor.paperSummariesFromSources')">
        <n-list v-if="paperSummaries.length" bordered>
          <n-list-item
            v-for="(item, index) in paperSummaries"
            :key="item.source_input_id || index"
          >
            <n-space vertical style="width: 100%">
              <div style="font-weight: 600">{{ item.title }}</div>
              <div style="color: var(--muted-foreground); font-size: 13px">
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
        <n-empty v-else :description="$t('professor.noPaperSummariesHint')" />
      </n-card>

      <n-card v-if="professor.research_profile" :title="$t('professor.researchProfile')">
        <template #header-extra>
          <n-space>
            <n-tag v-if="professor.research_profile_generated_at" type="success">
              {{ fmtDate(professor.research_profile_generated_at) }}
            </n-tag>
            <n-button
              size="small"
              :loading="generateProfileLoading"
              @click="handleGenerateProfile"
            >
              {{ $t('professor.regenerateProfile') }}
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
          <strong>{{ $t('professor.evidenceNotes') }}</strong>
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
          <strong>{{ $t('professor.conflictNotes') }}</strong>
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

      <n-card v-else :title="$t('professor.researchProfile')">
        <n-empty :description="$t('professor.noResearchProfileYet')">
          <template #extra>
            <n-button
              type="warning"
              :loading="generateProfileLoading"
              @click="handleGenerateProfile"
            >
              {{ $t('professor.generateProfile') }}
            </n-button>
          </template>
        </n-empty>
      </n-card>
    </n-space>

    <n-empty v-else-if="!loading" :description="$t('professor.professorMissing')" />
  </n-spin>
</template>
