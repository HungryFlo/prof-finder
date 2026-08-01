<script setup lang="ts">
import { inject, ref, onMounted, defineAsyncComponent, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NCard,
  NSpace,
  NButton,
  NForm,
  NFormItem,
  NInput,
  NDynamicTags,
  NSpin,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NDivider,
  NSelect,
  useMessage,
} from 'naive-ui'
import type { SelectOption } from 'naive-ui'
import { profilesApi } from '@/api/profiles'
const ProfileChatPanel = defineAsyncComponent(() => import('@/components/ProfileChatPanel.vue'))
import { poolsApi } from '@/api/pools'
import { useFormatDate } from '@/composables/useDateLocale'
import { useApiError } from '@/composables/useApiError'
import type { ExperiencePool, Profile, EducationItem, ResearchItem, ProjectItem } from '@/types'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const { t } = useI18n()
const { handleApiError } = useApiError()

const setBreadcrumbTitle = inject<(title: string) => void>('setBreadcrumbTitle', () => {})

const { formatDateTime } = useFormatDate()

const loading = ref(false)
const saving = ref(false)
const showChat = ref(false)
// The chat panel pulls in a large markdown/KaTeX chunk, so it is only mounted
// once the user actually opens it, then kept alive to preserve the transcript.
const chatMounted = ref(false)
watch(showChat, (visible) => {
  if (visible) chatMounted.value = true
})
const profile = ref<Profile | null>(null)
const profileId = ref(0)
const pools = ref<ExperiencePool[]>([])
const boundPoolId = ref<number | null>(null)

const formData = ref({
  title: '',
  name: '',
  name_locales: { zh: '', en: '' },
  skills: [] as string[],
  education: [] as EducationItem[],
  research_experience: [] as ResearchItem[],
  projects: [] as ProjectItem[],
})

const poolOptions = computed<SelectOption[]>(() =>
  pools.value.map((p) => ({ label: p.title, value: p.id }))
)

const boundPool = computed(() =>
  pools.value.find((p) => p.id === boundPoolId.value) ?? null
)

function sourceFormatDisplay(fmt: string | null | undefined): string {
  if (fmt === 'materials') return t('profile.sourceMaterials')
  if (!fmt || fmt === 'manual') return t('profile.manualInput')
  return fmt
}

async function fetchProfile() {
  const id = Number(route.params.id)
  if (!id) {
    message.error(t('profile.invalidProfileId'))
    router.push('/profile')
    return
  }

  loading.value = true
  try {
    profile.value = await profilesApi.get(id)
    profileId.value = id
    boundPoolId.value = profile.value.experience_pool_id ?? null
    setBreadcrumbTitle(profile.value.title)
    formData.value = {
      title: profile.value.title,
      name: profile.value.name || '',
      name_locales: {
        zh: profile.value.name_locales?.zh ?? '',
        en: profile.value.name_locales?.en ?? '',
      },
      skills: [...(profile.value.skills || [])],
      education: [...(profile.value.education || [])],
      research_experience: [...(profile.value.research_experience || [])],
      projects: [...(profile.value.projects || [])],
    }
  } catch (error: unknown) {
    handleApiError(error, t('profile.fetchDetailFailed'))
    router.push('/profile')
  } finally {
    loading.value = false
  }
}

async function fetchPools() {
  try {
    pools.value = await poolsApi.list()
  } catch {
    pools.value = []
  }
}

async function refreshProfileSilent() {
  if (!profileId.value) return
  try {
    const data = await profilesApi.get(profileId.value)
    profile.value = data
  } catch {
    // silent
  }
}

async function handleSave() {
  if (!profile.value) return

  saving.value = true
  try {
    const nl: Record<string, string> = {}
    const z = formData.value.name_locales.zh?.trim()
    const e = formData.value.name_locales.en?.trim()
    if (z) nl.zh = z
    if (e) nl.en = e

    await profilesApi.update(profile.value.id, {
      title: formData.value.title,
      name: formData.value.name || undefined,
      name_locales: nl,
      skills: formData.value.skills,
      education: formData.value.education,
      research_experience: formData.value.research_experience,
      projects: formData.value.projects,
      experience_pool_id: boundPoolId.value,
    })
    message.success(t('profile.saveSuccess'))
    await refreshProfileSilent()
  } catch (error: unknown) {
    handleApiError(error, t('profile.saveFailed'))
  } finally {
    saving.value = false
  }
}

function goBack() {
  router.push('/profile')
}

function formatNote(note: unknown): string {
  return typeof note === 'string' ? note : JSON.stringify(note)
}

onMounted(() => {
  fetchProfile()
  fetchPools()
})
</script>

<template>
  <n-spin :show="loading">
    <n-card v-if="profile">
      <template #header>
        <n-space justify="space-between" align="center">
          <span>{{ profile.title }}</span>
          <n-space>
            <n-tag v-if="profile.is_active" type="success">{{ $t('profile.active') }}</n-tag>
            <n-tag v-else type="default">{{ $t('profile.inactive') }}</n-tag>
          </n-space>
        </n-space>
      </template>

      <template #header-extra>
        <n-space>
          <n-button @click="goBack">{{ $t('profile.back') }}</n-button>
          <n-button
            v-if="profile.academic_profile"
            type="info"
            @click="showChat = true"
          >
            {{ $t('profile.aiOptimize') }}
          </n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">{{ $t('profile.save') }}</n-button>
        </n-space>
      </template>

      <n-descriptions :column="2" label-placement="left" bordered>
        <n-descriptions-item :label="$t('profile.sourceFormatLabel')">
          {{ sourceFormatDisplay(profile.source_format ?? undefined) }}
        </n-descriptions-item>
        <n-descriptions-item :label="$t('profile.createdAt')">
          {{ formatDateTime(profile.created_at) }}
        </n-descriptions-item>
        <n-descriptions-item :label="$t('pool.boundPool')" :span="2">
          <n-space align="center">
            <n-select
              v-model:value="boundPoolId"
              :options="poolOptions"
              clearable
              style="min-width: 240px"
              :placeholder="$t('pool.bindPoolNone')"
            />
            <n-button
              v-if="boundPool"
              size="small"
              @click="router.push(`/pool/${boundPool.id}`)"
            >
              {{ $t('pool.openBoundPool') }}
            </n-button>
            <span v-else style="color: var(--muted-foreground); font-size: 13px">
              {{ $t('pool.noBoundPool') }}
            </span>
          </n-space>
        </n-descriptions-item>
      </n-descriptions>

      <n-divider />

      <template v-if="profile.academic_profile">
        <n-divider>{{ $t('profile.academicProfile') }}</n-divider>
        <div
          style="white-space: pre-wrap; line-height: 1.7; font-size: 13px; padding: 12px; border: 1px solid var(--n-border-color); border-radius: 6px; background: var(--n-color-modal)"
        >
          {{ profile.academic_profile }}
        </div>

        <n-space v-if="profile.evidence_notes?.length" vertical style="margin-top: 16px">
          <strong>{{ $t('profile.evidenceNotes') }}</strong>
          <div>
            <n-tag
              v-for="(note, index) in profile.evidence_notes"
              :key="index"
              style="margin: 0 8px 8px 0"
            >
              {{ formatNote(note) }}
            </n-tag>
          </div>
        </n-space>

        <n-space v-if="profile.conflict_notes?.length" vertical style="margin-top: 16px">
          <strong>{{ $t('profile.conflictNotes') }}</strong>
          <div>
            <n-tag
              v-for="(note, index) in profile.conflict_notes"
              :key="index"
              type="warning"
              style="margin: 0 8px 8px 0"
            >
              {{ formatNote(note) }}
            </n-tag>
          </div>
        </n-space>
      </template>

      <n-form label-placement="top">
        <n-form-item :label="$t('profile.profileTitleLabel')">
          <n-input v-model:value="formData.title" :placeholder="$t('profile.profileTitlePlaceholder')" />
        </n-form-item>

        <n-form-item :label="$t('profile.name')">
          <n-input v-model:value="formData.name" :placeholder="$t('profile.namePlaceholder')" />
        </n-form-item>

        <n-form-item :label="$t('profile.nameLocaleZh')">
          <n-input v-model:value="formData.name_locales.zh" :placeholder="$t('profile.nameLocaleZh')" />
        </n-form-item>
        <n-form-item :label="$t('profile.nameLocaleEn')">
          <n-input v-model:value="formData.name_locales.en" :placeholder="$t('profile.nameLocaleEn')" />
        </n-form-item>

        <n-form-item :label="$t('profile.skills')">
          <n-dynamic-tags v-model:value="formData.skills" />
        </n-form-item>

        <n-divider>{{ $t('profile.educationSection') }}</n-divider>
        <div v-for="(edu, index) in formData.education" :key="index" class="education-item">
          <n-space>
            <n-input v-model:value="edu.degree" :placeholder="$t('profile.degreePh')" style="width: 120px" />
            <n-input v-model:value="edu.school" :placeholder="$t('profile.schoolPh')" style="width: 200px" />
            <n-input v-model:value="edu.major" :placeholder="$t('profile.majorPh')" style="width: 150px" />
            <n-input v-model:value="edu.period" :placeholder="$t('profile.periodPh')" style="width: 150px" />
            <n-button
              size="small"
              type="error"
              @click="formData.education.splice(index, 1)"
            >
              {{ $t('profile.delete') }}
            </n-button>
          </n-space>
        </div>
        <n-button
          dashed
          @click="formData.education.push({ degree: '', school: '', major: '', period: '' })"
        >
          {{ $t('profile.addEducation') }}
        </n-button>

        <n-divider>{{ $t('profile.researchSection') }}</n-divider>
        <div v-for="(exp, index) in formData.research_experience" :key="index" class="research-item">
          <n-space vertical style="width: 100%">
            <n-space>
              <n-input v-model:value="exp.title" :placeholder="$t('profile.researchTitlePh')" style="width: 200px" />
              <n-input v-model:value="exp.organization" :placeholder="$t('profile.organizationPh')" style="width: 200px" />
              <n-input v-model:value="exp.period" :placeholder="$t('profile.periodPh')" style="width: 150px" />
              <n-button
                size="small"
                type="error"
                @click="formData.research_experience.splice(index, 1)"
              >
                {{ $t('profile.delete') }}
              </n-button>
            </n-space>
            <n-input
              v-model:value="exp.description"
              type="textarea"
              :placeholder="$t('profile.descriptionPh')"
              :rows="2"
            />
          </n-space>
        </div>
        <n-button
          dashed
          @click="formData.research_experience.push({ title: '', organization: '', description: '', period: '' })"
        >
          {{ $t('profile.addResearch') }}
        </n-button>

        <n-divider>{{ $t('profile.projectsSection') }}</n-divider>
        <div v-for="(proj, index) in formData.projects" :key="index" class="project-item">
          <n-space vertical style="width: 100%">
            <n-space>
              <n-input v-model:value="proj.name" :placeholder="$t('profile.projectNamePh')" style="width: 300px" />
              <n-button
                size="small"
                type="error"
                @click="formData.projects.splice(index, 1)"
              >
                {{ $t('profile.delete') }}
              </n-button>
            </n-space>
            <n-input
              v-model:value="proj.description"
              type="textarea"
              :placeholder="$t('profile.projectDescPh')"
              :rows="2"
            />
          </n-space>
        </div>
        <n-button
          dashed
          @click="formData.projects.push({ name: '', description: '' })"
        >
          {{ $t('profile.addProject') }}
        </n-button>
      </n-form>
    </n-card>

    <ProfileChatPanel
      v-if="chatMounted && profileId"
      :profile-id="profileId"
      v-model:show="showChat"
      @profile-refreshed="refreshProfileSilent"
    />
  </n-spin>
</template>

<style scoped>
.education-item,
.research-item,
.project-item {
  margin-bottom: 16px;
}
</style>
