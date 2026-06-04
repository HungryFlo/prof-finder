<script setup lang="ts">
import { computed, h, inject, ref, watch } from 'vue'
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
  NTooltip,
  NTag,
  NDataTable,
  NRadioGroup,
  NRadio,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import SourceInputPanel from '@/components/SourceInputPanel.vue'
import { professorsApi } from '@/api/professors'
import { sourceInputsApi } from '@/api/source-inputs'
import { useApiError } from '@/composables/useApiError'
import { useTaskStore } from '@/stores/tasks'
import { useFormatDate } from '@/composables/useDateLocale'
import type { PaperSummary, Professor, Publication, SourceInput } from '@/types'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const taskStore = useTaskStore()
const { handleApiError } = useApiError()
const { t } = useI18n()

const setBreadcrumbTitle = inject<(title: string) => void>('setBreadcrumbTitle', () => {})

const { formatDateTime } = useFormatDate()

function parseProfessorId(raw: string | string[] | undefined): number | null {
  const s = Array.isArray(raw) ? raw[0] : raw
  const id = Number(s)
  return Number.isFinite(id) && id > 0 ? id : null
}

const professorId = computed(() => parseProfessorId(route.params.id))

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
  google_scholar_url: '',
  dblp_url: '',
  research_interests: [] as string[],
  manual_notes: '',
})

const refreshLoading = ref(false)
const refreshDblpLoading = ref(false)
const fillPublicationsLoading = ref(false)
const crawlHomepageLoading = ref(false)
const summarizeLoading = ref(false)
const generateProfileLoading = ref(false)

const selectedDblpCandidateId = ref<string>('')
const confirmDblpLoading = ref(false)

const applyScholarLoading = ref(false)
const applyDblpLoading = ref(false)

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

function pubSourceLabel(row: Publication): string {
  if (row.source === 'dblp') return t('professor.pubSourceDblp')
  if (row.source === 'scholar') return t('professor.pubSourceScholar')
  if (row.dblp_url) return t('professor.pubSourceDblp')
  return t('professor.pubSourceScholar')
}

const publicationColumns = computed<DataTableColumns<Publication>>(() => [
  {
    title: t('professor.pubColTitle'),
    key: 'title',
    width: 380,
    render(row) {
      const children: ReturnType<typeof h>[] = []
      const link = row.gscholar_url || row.dblp_url
      if (link) {
        children.push(
          h('a', {
            href: link,
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
  {
    title: t('professor.pubColSource'),
    key: 'source',
    width: 88,
    render(row) {
      return h(NTag, { size: 'tiny', type: row.source === 'dblp' ? 'info' : 'success' }, {
        default: () => pubSourceLabel(row),
      })
    },
  },
  { title: t('professor.pubColYear'), key: 'year', width: 72 },
  { title: t('professor.pubColCitations'), key: 'citations', width: 88 },
  {
    title: t('professor.pubColVenue'),
    key: 'journal',
    width: 200,
    render(row) {
      return row.venue || row.journal || row.conference || '-'
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
  const id = professorId.value
  if (id == null) {
    if (route.name === 'ProfessorDetail') {
      message.error(t('professor.invalidId'))
      router.push('/professor')
    }
    return
  }
  loading.value = true
  try {
    const [data, inputs] = await Promise.all([
      professorsApi.get(id),
      sourceInputsApi.listByProfessor(id).catch(() => []),
    ])
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
      google_scholar_url: data.google_scholar_url || '',
      dblp_url: data.dblp_url || '',
      research_interests: [...(data.research_interests || [])],
      manual_notes: data.manual_notes || '',
    }
    sourceInputs.value = inputs
  } catch (error: unknown) {
    handleApiError(error, t('professor.loadFailed'))
    router.push('/professor')
  } finally {
    loading.value = false
  }
}

function normalizeScholarUrl(url: string): string {
  return url.trim()
}

function scholarUrlChanged(): boolean {
  const next = normalizeScholarUrl(form.value.google_scholar_url)
  const prev = normalizeScholarUrl(professor.value?.google_scholar_url || '')
  return next !== prev
}

async function applyScholarUrlIfChanged(): Promise<void> {
  const url = normalizeScholarUrl(form.value.google_scholar_url)
  if (!url || !scholarUrlChanged() || !professor.value) return

  const { task_id } = await professorsApi.setScholarId(professor.value.id, url)
  message.success(t('professor.setScholarSuccess'))
  taskStore.addTask(
    task_id,
    'single-crawl',
    t('professor.importProfessorTask'),
    1,
    () => fetchData(),
  )
}

async function handleApplyScholarUrl() {
  const url = normalizeScholarUrl(form.value.google_scholar_url)
  if (!url) {
    message.warning(t('professor.scholarUrlRequired'))
    return
  }
  if (!scholarUrlChanged()) {
    message.info(t('professor.scholarUrlUnchanged'))
    return
  }
  applyScholarLoading.value = true
  try {
    await applyScholarUrlIfChanged()
  } catch (error: unknown) {
    handleApiError(error, t('professor.startTaskFailed'))
  } finally {
    applyScholarLoading.value = false
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
    const updated = await professorsApi.update(professorId.value, {
      name: form.value.name,
      name_locales: nl,
      affiliation: form.value.affiliation || undefined,
      email: form.value.email || undefined,
      homepage: form.value.homepage || undefined,
      research_interests: form.value.research_interests,
      manual_notes: form.value.manual_notes || undefined,
    })
    professor.value = updated
    if (normalizeScholarUrl(form.value.google_scholar_url) && scholarUrlChanged()) {
      await applyScholarUrlIfChanged()
    }
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
    const updated = await professorsApi.refresh(professorId.value)
    professor.value = updated
    setBreadcrumbTitle(updated.name)
    form.value = {
      name: updated.name,
      name_locales: {
        zh: updated.name_locales?.zh ?? '',
        en: updated.name_locales?.en ?? '',
      },
      affiliation: updated.affiliation || '',
      email: updated.email || '',
      homepage: updated.homepage || '',
      google_scholar_url: updated.google_scholar_url || '',
      research_interests: [...(updated.research_interests || [])],
      manual_notes: updated.manual_notes || '',
    }
    message.success(t('professor.scholarSynced'))
    // Re-fetch only source inputs (professor data already updated from refresh response)
    try {
      sourceInputs.value = await sourceInputsApi.listByProfessor(professorId.value)
    } catch {
      // non-critical
    }
  } catch (error: unknown) {
    handleApiError(error, t('professor.scholarSyncFailed'))
  } finally {
    refreshLoading.value = false
  }
}

const hasHomepageUrl = computed(() => Boolean(form.value.homepage?.trim()))

async function handleCrawlHomepage() {
  if (!professor.value || !professorId.value) return
  if (!hasHomepageUrl.value) {
    message.warning(t('professor.crawlHomepageNoUrl'))
    return
  }

  crawlHomepageLoading.value = true
  try {
    const { task_id } = await professorsApi.crawlHomepage(professorId.value)
    message.success(t('professor.crawlHomepageStarted'))
    taskStore.addTask(
      task_id,
      'professor-homepage-crawl',
      t('professor.crawlHomepageTask', { name: professor.value.name }),
      1,
      () => {
        fetchData()
      },
    )
  } catch (error: unknown) {
    handleApiError(error, t('professor.startTaskFailed'))
  } finally {
    crawlHomepageLoading.value = false
  }
}

async function handleFillPublications() {
  if (!professor.value || !professorId.value) return

  fillPublicationsLoading.value = true
  try {
    const { task_id, total } = await professorsApi.startFillPublications(professorId.value)
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
  if (!professor.value || !professorId.value) return

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
    const { task_id } = await professorsApi.startPaperSummary(professorId.value, pendingIds)
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
  if (!professor.value || !professorId.value) return

  generateProfileLoading.value = true
  try {
    const { task_id, message: msg } = await professorsApi.generateProfile(professorId.value)
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

function dblpUrlChanged(): boolean {
  return form.value.dblp_url.trim() !== (professor.value?.dblp_url || '').trim()
}

async function handleApplyDblpUrl() {
  const url = form.value.dblp_url.trim()
  if (!url || !professor.value) {
    message.warning(t('professor.enterDblpUrl'))
    return
  }
  if (!dblpUrlChanged()) {
    message.info(t('professor.scholarUrlUnchanged'))
    return
  }
  applyDblpLoading.value = true
  try {
    const { task_id } = await professorsApi.setDblp(professor.value.id, url)
    message.success(t('professor.setDblpSuccess'))
    taskStore.addTask(task_id, 'single-dblp-crawl', t('professor.importProfessorTask'), 1, () => fetchData())
  } catch (error: unknown) {
    handleApiError(error, t('professor.startTaskFailed'))
  } finally {
    applyDblpLoading.value = false
  }
}

async function handleRefreshDblp() {
  if (!professor.value?.dblp_pid) return
  refreshDblpLoading.value = true
  try {
    const updated = await professorsApi.refreshDblp(professor.value.id)
    professor.value = updated
    message.success(t('professor.dblpSynced'))
    if (updated.enrichment_task_id) {
      taskStore.addTask(
        updated.enrichment_task_id,
        'professor-enrichment',
        t('professor.enrichmentTask'),
        updated.enrichment_task_total ?? 0,
        () => fetchData(),
      )
    }
  } catch (error: unknown) {
    handleApiError(error, t('professor.dblpSyncFailed'))
  } finally {
    refreshDblpLoading.value = false
  }
}

async function handleConfirmDblp() {
  if (!selectedDblpCandidateId.value || !professor.value) return
  confirmDblpLoading.value = true
  try {
    const { task_id } = await professorsApi.confirmDblp(
      professor.value.id,
      selectedDblpCandidateId.value,
    )
    message.success(t('professor.confirmDblpSuccess'))
    taskStore.addTask(task_id, 'single-dblp-crawl', t('professor.importProfessorTask'), 1, () => fetchData())
  } catch (error: unknown) {
    handleApiError(error, t('professor.startTaskFailed'))
  } finally {
    confirmDblpLoading.value = false
  }
}

watch(
  () => [route.name, route.params.id] as const,
  ([name]) => {
    if (name !== 'ProfessorDetail') return
    professor.value = null
    fetchData()
  },
  { immediate: true },
)
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
            <n-space vertical style="width: 100%">
              <n-input v-model:value="form.homepage" />
              <n-tooltip :disabled="hasHomepageUrl">
                <template #trigger>
                  <n-button
                    size="small"
                    secondary
                    type="primary"
                    :disabled="!hasHomepageUrl"
                    :loading="crawlHomepageLoading"
                    @click="handleCrawlHomepage"
                  >
                    {{ $t('professor.crawlHomepage') }}
                  </n-button>
                </template>
                {{ $t('professor.crawlHomepageNoUrl') }}
              </n-tooltip>
            </n-space>
          </n-form-item>
          <n-form-item :label="$t('professor.scholarFormLabel')">
            <n-space vertical style="width: 100%">
              <n-input
                v-model:value="form.google_scholar_url"
                :placeholder="$t('professor.setScholarUrlPlaceholder')"
              />
              <n-space>
                <n-button
                  size="small"
                  type="primary"
                  secondary
                  :loading="applyScholarLoading"
                  @click="handleApplyScholarUrl"
                >
                  {{ $t('professor.applyScholarUrl') }}
                </n-button>
                <a
                  v-if="form.google_scholar_url"
                  :href="form.google_scholar_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  style="font-size: 13px"
                >
                  {{ $t('professor.scholarHome') }}
                </a>
              </n-space>
            </n-space>
          </n-form-item>
          <n-form-item :label="$t('professor.dblpFormLabel')">
            <n-space vertical style="width: 100%">
              <n-input
                v-model:value="form.dblp_url"
                :placeholder="$t('professor.setDblpUrlPlaceholder')"
              />
              <n-space>
                <n-button
                  size="small"
                  type="primary"
                  secondary
                  :loading="applyDblpLoading"
                  @click="handleApplyDblpUrl"
                >
                  {{ $t('professor.applyDblpUrl') }}
                </n-button>
                <a
                  v-if="form.dblp_url"
                  :href="form.dblp_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  style="font-size: 13px"
                >
                  {{ $t('professor.dblpHome') }}
                </a>
              </n-space>
            </n-space>
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

      <n-card
        v-if="professor.dblp_enrichment_status === 'ambiguous' && professor.dblp_candidates?.length"
        :title="$t('professor.dblpCandidates')"
      >
        <p style="color: var(--muted-foreground); margin-bottom: 12px; font-size: 13px">
          {{ $t('professor.dblpCandidatesDesc') }}
        </p>
        <n-radio-group v-model:value="selectedDblpCandidateId" style="width: 100%">
          <n-space vertical>
            <div
              v-for="c in professor.dblp_candidates"
              :key="c.pid"
              style="
                padding: 12px;
                border: 1px solid var(--n-border-color);
                border-radius: 6px;
                cursor: pointer;
              "
              :style="selectedDblpCandidateId === c.pid ? 'border-color: var(--primary-color)' : ''"
              @click="selectedDblpCandidateId = c.pid"
            >
              <n-radio :value="c.pid">
                <strong>{{ c.name }}</strong>
              </n-radio>
              <div style="margin-left: 24px; margin-top: 4px; font-size: 13px; color: var(--muted-foreground)">
                <span v-if="c.affiliation">{{ c.affiliation }}</span>
              </div>
            </div>
          </n-space>
        </n-radio-group>
        <n-space style="margin-top: 16px">
          <n-button
            type="primary"
            :disabled="!selectedDblpCandidateId"
            :loading="confirmDblpLoading"
            @click="handleConfirmDblp"
          >
            {{ $t('professor.confirmDblp') }}
          </n-button>
        </n-space>
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

      <n-card :title="$t('professor.publicationsMergedTitle')">
        <template #header-extra>
          <n-space>
            <n-popconfirm
              v-if="professor.dblp_pid"
              @positive-click="handleRefreshDblp"
            >
              <template #trigger>
                <n-button size="small" :loading="refreshDblpLoading">
                  {{ $t('professor.dblpSyncButton') }}
                </n-button>
              </template>
              {{ $t('professor.dblpResyncQuestion') }}
            </n-popconfirm>
            <n-popconfirm
              v-if="professor.google_scholar_id"
              @positive-click="handleRefreshScholar"
            >
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
              {{ formatDateTime(professor.research_profile_generated_at) }}
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
