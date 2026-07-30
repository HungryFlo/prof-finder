<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NButton,
  NCard,
  NCheckbox,
  NDrawer,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NPopconfirm,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  useMessage,
} from 'naive-ui'
import {
  CheckmarkCircleOutline,
  ChevronForwardOutline,
  EllipseOutline,
} from '@vicons/ionicons5'
import { useDebounceFn } from '@vueuse/core'
import { getLocale } from '@/i18n'
import { poolsApi } from '@/api/pools'
import { profilesApi } from '@/api/profiles'
import { useApiError } from '@/composables/useApiError'
import type {
  CompositionDocType,
  ExperienceCluster,
  ExperiencePool,
  ExperienceSeed,
  ExperienceStory,
  PoolComposition,
  PoolPhase,
  Profile,
} from '@/types'

const PHASE_ORDER: PoolPhase[] = ['brainstorm', 'cluster', 'detail', 'compose']

const route = useRoute()
const router = useRouter()
const message = useMessage()
const { t, tm } = useI18n()
const { handleApiError } = useApiError()
const setBreadcrumbTitle = inject<(title: string) => void>('setBreadcrumbTitle', () => {})

const loading = ref(true)
const poolId = ref(0)
const pool = ref<ExperiencePool | null>(null)
const phase = ref<PoolPhase>('brainstorm')
const guideCollapsed = ref(false)

const seeds = ref<ExperienceSeed[]>([])
const discardedSeeds = ref<ExperienceSeed[]>([])
const clusters = ref<ExperienceCluster[]>([])
const stories = ref<ExperienceStory[]>([])
const compositions = ref<PoolComposition[]>([])

const brainstormInput = ref('')
const batchPaste = ref('')
const showBatch = ref(false)
const showDiscarded = ref(false)

const draggingSeedId = ref<number | null>(null)
const newClusterTitle = ref('')

const selectedStorySeedId = ref<number | null>(null)
const storyDraft = ref({
  origin: '',
  process: '',
  outcome: '',
  problems: '',
  setbacks: '',
  knowledge: '',
  insights: '',
  freeform: '',
})

const selectedStoryIds = ref<number[]>([])
const composeDocType = ref<CompositionDocType>('resume_bullet')
const composeTitle = ref('')
const composeBody = ref('')
const editingCompositionId = ref<number | null>(null)
const generating = ref(false)
const profiles = ref<Profile[]>([])
const applyProfileId = ref<number | null>(null)
const showApplyModal = ref(false)
const applyTargetCompositionId = ref<number | null>(null)

const promptIndex = ref(0)
const brainstormPrompts = computed(() => {
  const list = tm('pool.brainstormPrompts')
  return Array.isArray(list) ? (list as string[]) : []
})

const activeSeeds = computed(() => seeds.value.filter((s) => s.status === 'active'))
const ungroupedSeeds = computed(() =>
  activeSeeds.value.filter((s) => s.cluster_id == null)
)
const selectedStory = computed(() =>
  stories.value.find((s) => s.seed_id === selectedStorySeedId.value) ?? null
)

const storyFields = [
  'origin',
  'process',
  'outcome',
  'problems',
  'setbacks',
  'knowledge',
  'insights',
  'freeform',
] as const

const docTypeOptions = computed(() => [
  { label: t('pool.docTypes.resume_bullet'), value: 'resume_bullet' },
  { label: t('pool.docTypes.personal_statement'), value: 'personal_statement' },
  { label: t('pool.docTypes.research_plan'), value: 'research_plan' },
  { label: t('pool.docTypes.letter_snippet'), value: 'letter_snippet' },
])

const profileOptions = computed(() =>
  profiles.value.map((p) => ({
    label: p.is_active ? `${p.title} (${t('profile.active')})` : p.title,
    value: p.id,
  }))
)

const phaseSteps = computed(() =>
  PHASE_ORDER.map((key) => ({
    key,
    label: t(`pool.phases.${key}`),
    desc: t(`pool.phaseDescs.${key}`),
  }))
)

const activePhaseIndex = computed(() => {
  const idx = PHASE_ORDER.indexOf(phase.value)
  return idx >= 0 ? idx : 0
})

async function loadAll() {
  const id = Number(route.params.id)
  if (!id) {
    message.error(t('pool.invalidId'))
    router.push('/pool')
    return
  }
  poolId.value = id
  loading.value = true
  try {
    pool.value = await poolsApi.get(id)
    setBreadcrumbTitle(pool.value.title)
    phase.value = (pool.value.phase as PoolPhase) || 'brainstorm'
    await Promise.all([refreshSeeds(), refreshClusters(), refreshStories(), refreshCompositions()])
  } catch (error: unknown) {
    handleApiError(error, t('pool.fetchFailed'))
    router.push('/pool')
  } finally {
    loading.value = false
  }
}

async function refreshSeeds() {
  const [active, discarded] = await Promise.all([
    poolsApi.listSeeds(poolId.value, 'active'),
    poolsApi.listSeeds(poolId.value, 'discarded'),
  ])
  seeds.value = active
  discardedSeeds.value = discarded
}

async function refreshClusters() {
  clusters.value = await poolsApi.listClusters(poolId.value)
}

async function refreshStories() {
  stories.value = await poolsApi.listStories(poolId.value)
  if (
    selectedStorySeedId.value &&
    !stories.value.some((s) => s.seed_id === selectedStorySeedId.value)
  ) {
    selectedStorySeedId.value = stories.value[0]?.seed_id ?? null
  }
  if (!selectedStorySeedId.value && stories.value.length) {
    selectedStorySeedId.value = stories.value[0].seed_id
  }
  syncStoryDraft()
}

async function refreshCompositions() {
  compositions.value = await poolsApi.listCompositions(poolId.value)
}

function syncStoryDraft() {
  const story = selectedStory.value
  if (!story) {
    storyDraft.value = {
      origin: '',
      process: '',
      outcome: '',
      problems: '',
      setbacks: '',
      knowledge: '',
      insights: '',
      freeform: '',
    }
    return
  }
  storyDraft.value = {
    origin: story.origin || '',
    process: story.process || '',
    outcome: story.outcome || '',
    problems: story.problems || '',
    setbacks: story.setbacks || '',
    knowledge: story.knowledge || '',
    insights: story.insights || '',
    freeform: story.freeform || '',
  }
}

watch(selectedStorySeedId, syncStoryDraft)

async function setPhase(next: PoolPhase) {
  phase.value = next
  try {
    pool.value = await poolsApi.update(poolId.value, { phase: next })
  } catch (error: unknown) {
    handleApiError(error, t('pool.updateFailed'))
  }
  if (next === 'detail') await refreshStories()
  if (next === 'compose') {
    await Promise.all([refreshStories(), refreshCompositions(), loadProfiles()])
  }
}

async function loadProfiles() {
  try {
    profiles.value = await profilesApi.list()
  } catch {
    profiles.value = []
  }
}

async function addSeed() {
  const content = brainstormInput.value.trim()
  if (!content) return
  try {
    await poolsApi.createSeed(poolId.value, { content })
    brainstormInput.value = ''
    await refreshSeeds()
  } catch (error: unknown) {
    handleApiError(error, t('pool.seedCreateFailed'))
  }
}

async function submitBatch() {
  const lines = batchPaste.value
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean)
  if (!lines.length) {
    message.warning(t('pool.batchEmpty'))
    return
  }
  try {
    await poolsApi.createSeedsBatch(poolId.value, lines)
    batchPaste.value = ''
    showBatch.value = false
    message.success(t('pool.batchSuccess', { count: lines.length }))
    await refreshSeeds()
  } catch (error: unknown) {
    handleApiError(error, t('pool.seedCreateFailed'))
  }
}

async function discardSeed(seedId: number) {
  try {
    await poolsApi.updateSeed(poolId.value, seedId, { status: 'discarded', clear_cluster: true })
    await refreshSeeds()
  } catch (error: unknown) {
    handleApiError(error, t('pool.seedUpdateFailed'))
  }
}

async function restoreSeed(seedId: number) {
  try {
    await poolsApi.updateSeed(poolId.value, seedId, { status: 'active' })
    await refreshSeeds()
  } catch (error: unknown) {
    handleApiError(error, t('pool.seedUpdateFailed'))
  }
}

async function toggleStandalone(seed: ExperienceSeed) {
  try {
    await poolsApi.updateSeed(poolId.value, seed.id, { standalone: !seed.standalone })
    await refreshSeeds()
  } catch (error: unknown) {
    handleApiError(error, t('pool.seedUpdateFailed'))
  }
}

async function createCluster() {
  const title = newClusterTitle.value.trim()
  if (!title) {
    message.warning(t('pool.clusterTitleRequired'))
    return
  }
  try {
    await poolsApi.createCluster(poolId.value, { title })
    newClusterTitle.value = ''
    await refreshClusters()
  } catch (error: unknown) {
    handleApiError(error, t('pool.clusterCreateFailed'))
  }
}

async function renameCluster(cluster: ExperienceCluster) {
  const title = window.prompt(t('pool.renameCluster'), cluster.title)
  if (title == null || !title.trim()) return
  try {
    await poolsApi.updateCluster(poolId.value, cluster.id, { title: title.trim() })
    await refreshClusters()
  } catch (error: unknown) {
    handleApiError(error, t('pool.clusterUpdateFailed'))
  }
}

async function deleteCluster(clusterId: number) {
  try {
    await poolsApi.deleteCluster(poolId.value, clusterId)
    await Promise.all([refreshClusters(), refreshSeeds()])
  } catch (error: unknown) {
    handleApiError(error, t('pool.clusterDeleteFailed'))
  }
}

function onDragStart(seedId: number, event: DragEvent) {
  draggingSeedId.value = seedId
  event.dataTransfer?.setData('text/plain', String(seedId))
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDragEnd() {
  draggingSeedId.value = null
}

async function dropOnCluster(clusterId: number | null) {
  const seedId = draggingSeedId.value
  draggingSeedId.value = null
  if (seedId == null) return
  try {
    if (clusterId == null) {
      await poolsApi.updateSeed(poolId.value, seedId, { clear_cluster: true })
    } else {
      await poolsApi.updateSeed(poolId.value, seedId, { cluster_id: clusterId })
    }
    await refreshSeeds()
  } catch (error: unknown) {
    handleApiError(error, t('pool.seedUpdateFailed'))
  }
}

function seedsInCluster(clusterId: number) {
  return activeSeeds.value.filter((s) => s.cluster_id === clusterId)
}

function selectStory(seedId: number) {
  selectedStorySeedId.value = seedId
}

const saveStoryDebounced = useDebounceFn(async () => {
  if (!selectedStorySeedId.value) return
  try {
    const updated = await poolsApi.updateStory(poolId.value, selectedStorySeedId.value, {
      ...storyDraft.value,
    })
    const idx = stories.value.findIndex((s) => s.seed_id === updated.seed_id)
    if (idx >= 0) stories.value[idx] = updated
  } catch (error: unknown) {
    handleApiError(error, t('pool.storySaveFailed'))
  }
}, 600)

function onStoryFieldInput() {
  void saveStoryDebounced()
}

function goNextStory() {
  if (!stories.value.length || selectedStorySeedId.value == null) return
  const idx = stories.value.findIndex((s) => s.seed_id === selectedStorySeedId.value)
  const next = stories.value[(idx + 1) % stories.value.length]
  selectedStorySeedId.value = next.seed_id
}

function completionTagType(completion: string) {
  if (completion === 'complete') return 'success'
  if (completion === 'partial') return 'warning'
  return 'default'
}

function toggleStorySelect(storyId: number, checked: boolean) {
  if (checked) {
    if (!selectedStoryIds.value.includes(storyId)) selectedStoryIds.value.push(storyId)
  } else {
    selectedStoryIds.value = selectedStoryIds.value.filter((id) => id !== storyId)
  }
}

async function saveManualComposition() {
  if (!composeTitle.value.trim()) {
    message.warning(t('pool.compositionTitleRequired'))
    return
  }
  try {
    if (editingCompositionId.value) {
      await poolsApi.updateComposition(poolId.value, editingCompositionId.value, {
        doc_type: composeDocType.value,
        title: composeTitle.value.trim(),
        body: composeBody.value,
        source_story_ids: selectedStoryIds.value,
      })
      message.success(t('pool.compositionUpdated'))
    } else {
      await poolsApi.createComposition(poolId.value, {
        doc_type: composeDocType.value,
        title: composeTitle.value.trim(),
        body: composeBody.value,
        source_story_ids: selectedStoryIds.value,
      })
      message.success(t('pool.compositionCreated'))
    }
    editingCompositionId.value = null
    composeTitle.value = ''
    composeBody.value = ''
    await refreshCompositions()
  } catch (error: unknown) {
    handleApiError(error, t('pool.compositionSaveFailed'))
  }
}

async function generateDraft() {
  if (!selectedStoryIds.value.length) {
    message.warning(t('pool.selectStoriesFirst'))
    return
  }
  generating.value = true
  try {
    const result = await poolsApi.generateComposition(poolId.value, {
      doc_type: composeDocType.value,
      story_ids: selectedStoryIds.value,
      title: composeTitle.value.trim() || undefined,
      language: getLocale() === 'zh' ? 'zh' : 'en',
    })
    editingCompositionId.value = result.id
    composeTitle.value = result.title
    composeBody.value = result.body
    composeDocType.value = result.doc_type as CompositionDocType
    message.success(t('pool.generateDraftSuccess'))
    await refreshCompositions()
  } catch (error: unknown) {
    handleApiError(error, t('pool.generateDraftFailed'))
  } finally {
    generating.value = false
  }
}

function editComposition(item: PoolComposition) {
  editingCompositionId.value = item.id
  composeTitle.value = item.title
  composeBody.value = item.body
  composeDocType.value = item.doc_type as CompositionDocType
  selectedStoryIds.value = [...(item.source_story_ids || [])]
}

async function deleteComposition(id: number) {
  try {
    await poolsApi.deleteComposition(poolId.value, id)
    if (editingCompositionId.value === id) {
      editingCompositionId.value = null
      composeTitle.value = ''
      composeBody.value = ''
    }
    message.success(t('pool.compositionDeleted'))
    await refreshCompositions()
  } catch (error: unknown) {
    handleApiError(error, t('pool.compositionDeleteFailed'))
  }
}

async function copyComposition(body: string) {
  try {
    await navigator.clipboard.writeText(body)
    message.success(t('common.copySuccess'))
  } catch {
    message.error(t('common.copyFailed'))
  }
}

function openApply(compositionId: number) {
  applyTargetCompositionId.value = compositionId
  applyProfileId.value = profiles.value.find((p) => p.is_active)?.id ?? profiles.value[0]?.id ?? null
  showApplyModal.value = true
}

async function confirmApply() {
  if (!applyTargetCompositionId.value || !applyProfileId.value) {
    message.warning(t('pool.selectProfileFirst'))
    return
  }
  try {
    const result = await poolsApi.applyComposition(
      poolId.value,
      applyTargetCompositionId.value,
      applyProfileId.value
    )
    message.success(result.message || t('pool.applySuccess'))
    showApplyModal.value = false
  } catch (error: unknown) {
    handleApiError(error, t('pool.applyFailed'))
  }
}

function nextPrompt() {
  const list = brainstormPrompts.value
  if (!list?.length) return
  promptIndex.value = (promptIndex.value + 1) % list.length
}

onMounted(loadAll)
</script>

<template>
  <div>
    <n-spin :show="loading">
      <n-card v-if="pool">
        <template #header>
          <div class="workspace-header">
            <div>
              <h2 class="workspace-title">{{ pool.title }}</h2>
              <p v-if="pool.description" class="workspace-desc">{{ pool.description }}</p>
            </div>
            <n-button quaternary @click="router.push('/pool')">{{ $t('pool.backToList') }}</n-button>
          </div>
        </template>

        <div class="phase-flow">
          <button
            v-for="(step, i) in phaseSteps"
            :key="step.key"
            type="button"
            class="phase-flow__step"
            :class="{
              'phase-flow__step--done': i < activePhaseIndex,
              'phase-flow__step--active': i === activePhaseIndex,
            }"
            @click="setPhase(step.key)"
          >
            <div class="phase-flow__indicator">
              <div v-if="i < activePhaseIndex" class="phase-flow__check">
                <n-icon :size="16"><CheckmarkCircleOutline /></n-icon>
              </div>
              <div v-else-if="i === activePhaseIndex" class="phase-flow__pulse" />
              <div v-else class="phase-flow__circle">
                <n-icon :size="14"><EllipseOutline /></n-icon>
              </div>
            </div>
            <div class="phase-flow__content">
              <span class="phase-flow__label">{{ step.label }}</span>
              <span class="phase-flow__desc">{{ step.desc }}</span>
            </div>
            <n-icon
              v-if="i < phaseSteps.length - 1"
              :size="14"
              class="phase-flow__arrow"
            >
              <ChevronForwardOutline />
            </n-icon>
          </button>
        </div>

        <div class="guide-bar">
          <button class="guide-toggle" type="button" @click="guideCollapsed = !guideCollapsed">
            {{ guideCollapsed ? $t('pool.showGuide') : $t('pool.hideGuide') }}
          </button>
          <p v-if="!guideCollapsed" class="guide-text">{{ $t(`pool.guides.${phase}`) }}</p>
        </div>

        <!-- Brainstorm -->
        <div v-if="phase === 'brainstorm'" class="phase-panel">
          <div class="prompt-card">
            <span>{{ brainstormPrompts[promptIndex] }}</span>
            <n-button size="tiny" @click="nextPrompt">{{ $t('pool.nextPrompt') }}</n-button>
          </div>
          <n-space vertical style="width: 100%">
            <n-input
              v-model:value="brainstormInput"
              :placeholder="$t('pool.seedPlaceholder')"
              @keydown.enter.prevent="addSeed"
            />
            <n-space>
              <n-button type="primary" @click="addSeed">{{ $t('pool.addSeed') }}</n-button>
              <n-button @click="showBatch = true">{{ $t('pool.batchPaste') }}</n-button>
              <n-button @click="showDiscarded = true">
                {{ $t('pool.discardedDrawer') }} ({{ discardedSeeds.length }})
              </n-button>
            </n-space>
          </n-space>

          <div class="seed-grid">
            <div v-for="seed in activeSeeds" :key="seed.id" class="seed-card">
              <div class="seed-content">{{ seed.content }}</div>
              <n-space size="small">
                <n-button size="tiny" @click="discardSeed(seed.id)">{{ $t('pool.discard') }}</n-button>
              </n-space>
            </div>
            <div v-if="!activeSeeds.length" class="empty-hint">{{ $t('pool.brainstormEmpty') }}</div>
          </div>
        </div>

        <!-- Cluster kanban -->
        <div v-else-if="phase === 'cluster'" class="phase-panel">
          <n-space style="margin-bottom: 12px">
            <n-input
              v-model:value="newClusterTitle"
              :placeholder="$t('pool.newClusterPlaceholder')"
              style="width: 220px"
              @keydown.enter.prevent="createCluster"
            />
            <n-button type="primary" @click="createCluster">{{ $t('pool.addCluster') }}</n-button>
          </n-space>

          <div class="kanban">
            <div
              class="kanban-col kanban-col--ungrouped"
              @dragover.prevent
              @drop.prevent="dropOnCluster(null)"
            >
              <div class="kanban-col-title">{{ $t('pool.ungrouped') }}</div>
              <div class="kanban-seed-list">
                <div
                  v-for="seed in ungroupedSeeds"
                  :key="seed.id"
                  class="seed-card draggable"
                  draggable="true"
                  @dragstart="onDragStart(seed.id, $event)"
                  @dragend="onDragEnd"
                >
                  <div class="seed-content">{{ seed.content }}</div>
                  <n-space size="small">
                    <n-button size="tiny" @click="toggleStandalone(seed)">
                      {{ seed.standalone ? $t('pool.unmarkStandalone') : $t('pool.markStandalone') }}
                    </n-button>
                    <n-button size="tiny" @click="discardSeed(seed.id)">{{ $t('pool.discard') }}</n-button>
                  </n-space>
                  <n-tag v-if="seed.standalone" size="tiny" type="info" style="margin-top: 6px">
                    {{ $t('pool.standalone') }}
                  </n-tag>
                </div>
              </div>
            </div>

            <div class="kanban-clusters">
              <div
                v-for="cluster in clusters"
                :key="cluster.id"
                class="kanban-col"
                @dragover.prevent
                @drop.prevent="dropOnCluster(cluster.id)"
              >
                <div class="kanban-col-title">
                  <span>{{ cluster.title }}</span>
                  <n-space size="small">
                    <n-button size="tiny" quaternary @click="renameCluster(cluster)">
                      {{ $t('common.edit') }}
                    </n-button>
                    <n-popconfirm @positive-click="deleteCluster(cluster.id)">
                      <template #trigger>
                        <n-button size="tiny" quaternary type="error">{{ $t('common.delete') }}</n-button>
                      </template>
                      {{ $t('pool.deleteClusterConfirm') }}
                    </n-popconfirm>
                  </n-space>
                </div>
                <div
                  v-for="seed in seedsInCluster(cluster.id)"
                  :key="seed.id"
                  class="seed-card draggable"
                  draggable="true"
                  @dragstart="onDragStart(seed.id, $event)"
                  @dragend="onDragEnd"
                >
                  <div class="seed-content">{{ seed.content }}</div>
                  <n-space size="small">
                    <n-button size="tiny" @click="discardSeed(seed.id)">{{ $t('pool.discard') }}</n-button>
                  </n-space>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Detail -->
        <div v-else-if="phase === 'detail'" class="phase-panel detail-layout">
          <aside class="story-list">
            <div v-if="!stories.length" class="empty-hint">{{ $t('pool.detailEmpty') }}</div>
            <button
              v-for="story in stories"
              :key="story.seed_id"
              type="button"
              class="story-list-item"
              :class="{ active: story.seed_id === selectedStorySeedId }"
              @click="selectStory(story.seed_id)"
            >
              <div class="story-list-title">{{ story.seed_content }}</div>
              <n-space size="small">
                <n-tag size="tiny" :type="completionTagType(story.completion)">
                  {{ $t(`pool.completion.${story.completion}`) }}
                </n-tag>
                <n-tag v-if="story.cluster_title" size="tiny">{{ story.cluster_title }}</n-tag>
              </n-space>
            </button>
          </aside>
          <section class="story-editor" v-if="selectedStory">
            <div class="story-editor-header">
              <h3>{{ selectedStory.seed_content }}</h3>
              <n-button size="small" @click="goNextStory">{{ $t('pool.nextStory') }}</n-button>
            </div>
            <n-form label-placement="top">
              <n-form-item
                v-for="field in storyFields"
                :key="field"
                :label="$t(`pool.storyFields.${field}`)"
              >
                <n-input
                  v-model:value="storyDraft[field]"
                  type="textarea"
                  :rows="3"
                  :placeholder="$t(`pool.storyHints.${field}`)"
                  @update:value="onStoryFieldInput"
                />
              </n-form-item>
            </n-form>
            <p class="autosave-hint">{{ $t('pool.autosaveHint') }}</p>
          </section>
          <section v-else class="story-editor empty-hint">{{ $t('pool.detailEmpty') }}</section>
        </div>

        <!-- Compose -->
        <div v-else class="phase-panel compose-layout">
          <div class="compose-sources">
            <h3>{{ $t('pool.selectStories') }}</h3>
            <div v-if="!stories.length" class="empty-hint">{{ $t('pool.composeNoStories') }}</div>
            <label
              v-for="story in stories"
              :key="story.id"
              class="compose-story-row"
            >
              <n-checkbox
                :checked="selectedStoryIds.includes(story.id)"
                @update:checked="(v: boolean) => toggleStorySelect(story.id, v)"
              />
              <span>{{ story.seed_content }}</span>
            </label>
          </div>
          <div class="compose-editor">
            <n-form label-placement="top">
              <n-form-item :label="$t('pool.docType')">
                <n-select v-model:value="composeDocType" :options="docTypeOptions" />
              </n-form-item>
              <n-form-item :label="$t('pool.compositionTitle')">
                <n-input v-model:value="composeTitle" />
              </n-form-item>
              <n-form-item :label="$t('pool.compositionBody')">
                <n-input v-model:value="composeBody" type="textarea" :rows="10" />
              </n-form-item>
            </n-form>
            <n-space>
              <n-button type="primary" @click="saveManualComposition">
                {{ editingCompositionId ? $t('common.save') : $t('pool.saveComposition') }}
              </n-button>
              <n-button :loading="generating" @click="generateDraft">
                {{ $t('pool.generateDraft') }}
              </n-button>
            </n-space>

            <h3 style="margin-top: 24px">{{ $t('pool.compositionList') }}</h3>
            <div v-for="item in compositions" :key="item.id" class="composition-card">
              <div class="composition-meta">
                <strong>{{ item.title }}</strong>
                <n-tag size="tiny">{{ $t(`pool.docTypes.${item.doc_type}`) }}</n-tag>
              </div>
              <pre class="composition-body">{{ item.body }}</pre>
              <n-space size="small">
                <n-button size="tiny" @click="editComposition(item)">{{ $t('common.edit') }}</n-button>
                <n-button size="tiny" @click="copyComposition(item.body)">{{ $t('pool.copy') }}</n-button>
                <n-button size="tiny" type="primary" @click="openApply(item.id)">
                  {{ $t('pool.applyToProfile') }}
                </n-button>
                <n-popconfirm @positive-click="deleteComposition(item.id)">
                  <template #trigger>
                    <n-button size="tiny" type="error">{{ $t('common.delete') }}</n-button>
                  </template>
                  {{ $t('pool.deleteCompositionConfirm') }}
                </n-popconfirm>
              </n-space>
            </div>
          </div>
        </div>
      </n-card>
    </n-spin>

    <n-modal
      v-model:show="showBatch"
      preset="dialog"
      :title="$t('pool.batchPaste')"
      :positive-text="$t('common.confirm')"
      :negative-text="$t('common.cancel')"
      @positive-click="submitBatch"
      style="width: 560px"
    >
      <n-input
        v-model:value="batchPaste"
        type="textarea"
        :rows="8"
        :placeholder="$t('pool.batchPlaceholder')"
      />
    </n-modal>

    <n-drawer v-model:show="showDiscarded" :width="360" placement="right">
      <div style="padding: 16px">
        <h3>{{ $t('pool.discardedDrawer') }}</h3>
        <div v-for="seed in discardedSeeds" :key="seed.id" class="seed-card" style="margin-top: 8px">
          <div class="seed-content">{{ seed.content }}</div>
          <n-button size="tiny" @click="restoreSeed(seed.id)">{{ $t('pool.restore') }}</n-button>
        </div>
        <div v-if="!discardedSeeds.length" class="empty-hint">{{ $t('common.noData') }}</div>
      </div>
    </n-drawer>

    <n-modal
      v-model:show="showApplyModal"
      preset="dialog"
      :title="$t('pool.applyToProfile')"
      :positive-text="$t('common.confirm')"
      :negative-text="$t('common.cancel')"
      @positive-click="confirmApply"
    >
      <n-form label-placement="top">
        <n-form-item :label="$t('pool.selectProfile')">
          <n-select v-model:value="applyProfileId" :options="profileOptions" />
        </n-form-item>
        <p class="guide-text">{{ $t('pool.applyHint') }}</p>
      </n-form>
    </n-modal>
  </div>
</template>

<style scoped>
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.workspace-title {
  margin: 0;
  font-size: 20px;
}
.workspace-desc {
  margin: 4px 0 0;
  color: var(--muted-foreground);
  font-size: 13px;
}
.phase-flow {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--card);
  margin-bottom: 4px;
}
.phase-flow__step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s ease;
  position: relative;
  border: none;
  border-right: 1px solid var(--border);
  background: transparent;
  text-align: left;
  color: inherit;
  font: inherit;
  min-width: 0;
}
.phase-flow__step:last-child {
  border-right: none;
}
.phase-flow__step:hover {
  background: var(--accent);
}
.phase-flow__step--active {
  background: oklch(from var(--primary) l c h / 0.06);
}
.phase-flow__step--done {
  opacity: 0.7;
}
.phase-flow__step--done:hover {
  opacity: 1;
}
.phase-flow__indicator {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.phase-flow__check {
  color: var(--primary);
  display: flex;
}
.phase-flow__circle {
  color: var(--muted-foreground);
  display: flex;
}
.phase-flow__pulse {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--primary);
  position: relative;
}
.phase-flow__pulse::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid var(--primary);
  opacity: 0.3;
  animation: phase-pulse 2s ease-in-out infinite;
}
@keyframes phase-pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.2); opacity: 0; }
}
.phase-flow__content {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}
.phase-flow__label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--foreground);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.phase-flow__desc {
  font-size: 0.65rem;
  color: var(--muted-foreground);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.phase-flow__arrow {
  color: var(--muted-foreground);
  margin-left: auto;
  flex-shrink: 0;
  opacity: 0.35;
}
.phase-flow__step:hover .phase-flow__arrow {
  opacity: 1;
}
.guide-bar {
  margin: 8px 0 16px;
}
.guide-toggle {
  border: none;
  background: transparent;
  color: var(--primary);
  cursor: pointer;
  padding: 0;
  font-size: 13px;
}
.guide-text {
  margin: 8px 0 0;
  color: var(--muted-foreground);
  font-size: 14px;
  line-height: 1.5;
}
.phase-panel {
  min-height: 320px;
}
.prompt-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  margin-bottom: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--card);
  font-size: 14px;
}
.seed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
  margin-top: 16px;
}
.seed-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  background: var(--card);
}
.seed-card.draggable {
  cursor: grab;
}
.seed-content {
  font-size: 14px;
  margin-bottom: 8px;
  white-space: pre-wrap;
  word-break: break-word;
}
.kanban {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.kanban-col {
  border: 1px dashed var(--border);
  border-radius: 10px;
  padding: 10px;
  background: color-mix(in srgb, var(--card) 80%, transparent);
  min-height: 160px;
  min-width: 0;
}
.kanban-col--ungrouped {
  min-height: 120px;
}
.kanban-seed-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}
.kanban-clusters {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  align-items: start;
}
.kanban-col-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  margin-bottom: 10px;
  gap: 6px;
}
.kanban-col .seed-card {
  margin-bottom: 8px;
}
.kanban-col--ungrouped .seed-card {
  margin-bottom: 0;
}
.detail-layout,
.compose-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
}
.story-list,
.compose-sources {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px;
  max-height: 640px;
  overflow: auto;
}
.story-list-item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
}
.story-list-item.active,
.story-list-item:hover {
  background: color-mix(in srgb, var(--primary) 12%, transparent);
}
.story-list-title {
  font-size: 13px;
  margin-bottom: 6px;
}
.story-editor,
.compose-editor {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
}
.story-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.story-editor-header h3 {
  margin: 0;
  font-size: 16px;
}
.autosave-hint,
.empty-hint {
  color: var(--muted-foreground);
  font-size: 13px;
}
.compose-story-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  font-size: 13px;
}
.composition-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin-top: 10px;
}
.composition-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.composition-body {
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 13px;
  margin: 0 0 10px;
  max-height: 160px;
  overflow: auto;
}
@media (max-width: 900px) {
  .detail-layout,
  .compose-layout {
    grid-template-columns: 1fr;
  }
  .phase-flow {
    flex-direction: column;
  }
  .phase-flow__step {
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
  .phase-flow__step:last-child {
    border-bottom: none;
  }
}

:root.dark .phase-flow__step--active {
  background: oklch(from var(--primary) l c h / 0.1);
}
</style>
