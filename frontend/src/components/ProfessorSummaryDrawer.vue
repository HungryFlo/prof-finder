<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NButton,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NDrawer,
  NDrawerContent,
  NSpace,
  NSpin,
  NTag,
  useMessage,
} from 'naive-ui'
import { professorsApi } from '@/api/professors'
import type { Professor } from '@/types'

const props = defineProps<{
  show: boolean
  professorId: number
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'close'): void
}>()

const router = useRouter()
const message = useMessage()
const { t, locale } = useI18n()

const dateLocale = computed(() => (locale.value === 'en' ? 'en-US' : 'zh-CN'))

const loading = ref(false)
const professor = ref<Professor | null>(null)

function fmtDate(iso: string | null | undefined) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(dateLocale.value)
}

watch(
  () => [props.show, props.professorId] as const,
  async ([show, id]) => {
    if (show && id) {
      loading.value = true
      try {
        professor.value = await professorsApi.get(id)
      } catch (error: unknown) {
        const err = error as { response?: { data?: { detail?: string } } }
        message.error(err.response?.data?.detail || t('professor.drawerLoadFailed'))
        emit('update:show', false)
      } finally {
        loading.value = false
      }
    }
  }
)

function handleViewDetail() {
  if (professor.value) {
    emit('update:show', false)
    router.push(`/professor/${professor.value.id}`)
  }
}

function formatJsonNote(note: unknown): string {
  return typeof note === 'string' ? note : JSON.stringify(note)
}
</script>

<template>
  <n-drawer :show="show" :width="480" @update:show="(val: boolean) => emit('update:show', val)">
    <n-drawer-content
      v-if="professor"
      :title="professor.name"
      :native-scrollbar="false"
    >
      <n-spin :show="loading">
        <n-descriptions :column="1" label-placement="left" bordered>
          <n-descriptions-item :label="$t('professor.affiliation')">
            {{ professor.affiliation || '-' }}
          </n-descriptions-item>
          <n-descriptions-item :label="$t('professor.email')">
            {{ professor.email || '-' }}
          </n-descriptions-item>
          <n-descriptions-item :label="$t('professor.homepage')">
            <a
              v-if="professor.homepage"
              :href="professor.homepage"
              target="_blank"
            >
              {{ professor.homepage }}
            </a>
            <span v-else>-</span>
          </n-descriptions-item>
          <n-descriptions-item :label="$t('professor.googleScholar')">
            <a
              v-if="professor.google_scholar_url"
              :href="professor.google_scholar_url"
              target="_blank"
            >
              {{ $t('professor.scholarHome') }}
            </a>
            <span v-else>-</span>
          </n-descriptions-item>
          <n-descriptions-item :label="$t('professor.hIndex')">
            {{ professor.h_index ?? '-' }}
          </n-descriptions-item>
          <n-descriptions-item :label="$t('professor.totalCitations')">
            {{ professor.total_citations ?? '-' }}
          </n-descriptions-item>
          <n-descriptions-item :label="$t('professor.researchInterests')">
            <n-space size="small">
              <n-tag
                v-for="interest in professor.research_interests"
                :key="interest"
                type="info"
                size="small"
              >
                {{ interest }}
              </n-tag>
            </n-space>
            <span v-if="!professor.research_interests?.length">-</span>
          </n-descriptions-item>
        </n-descriptions>

        <template v-if="professor.research_profile">
          <n-divider />
          <h4 style="margin: 8px 0 12px">
            {{ $t('professor.researchProfile') }}
            <n-tag
              v-if="professor.research_profile_generated_at"
              size="small"
              type="success"
              style="margin-left: 8px"
            >
              {{ fmtDate(professor.research_profile_generated_at) }}
            </n-tag>
          </h4>
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
            style="margin-top: 12px"
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
            style="margin-top: 12px"
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
        </template>

        <n-divider />
        <n-space justify="end">
          <n-button type="primary" @click="handleViewDetail">
            {{ $t('professor.drawerOpenDetail') }}
          </n-button>
        </n-space>
      </n-spin>
    </n-drawer-content>
  </n-drawer>
</template>
