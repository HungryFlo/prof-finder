<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
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
  useMessage,
} from 'naive-ui'
import { profilesApi } from '@/api/profiles'
import ProfileChatPanel from '@/components/ProfileChatPanel.vue'
import type { Profile, EducationItem, ResearchItem, ProjectItem } from '@/types'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const { t, locale } = useI18n()

const dateLocale = computed(() => (locale.value === 'en' ? 'en-US' : 'zh-CN'))

const loading = ref(false)
const saving = ref(false)
const showChat = ref(false)
const profile = ref<Profile | null>(null)
const profileId = ref(0)

const formData = ref({
  title: '',
  name: '',
  name_locales: { zh: '', en: '' },
  skills: [] as string[],
  education: [] as EducationItem[],
  research_experience: [] as ResearchItem[],
  projects: [] as ProjectItem[],
})

function sourceFormatDisplay(fmt: string | null | undefined): string {
  if (fmt === 'materials') return t('profile.sourceMaterials')
  if (!fmt || fmt === 'manual') return t('profile.manualInput')
  return fmt
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleString(dateLocale.value)
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
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('profile.fetchDetailFailed'))
    router.push('/profile')
  } finally {
    loading.value = false
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
    })
    message.success(t('profile.saveSuccess'))
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('profile.saveFailed'))
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
            :type="showChat ? 'default' : 'info'"
            @click="showChat = !showChat"
          >
            {{ showChat ? $t('profile.collapseAi') : $t('profile.aiOptimize') }}
          </n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">{{ $t('profile.save') }}</n-button>
        </n-space>
      </template>

      <n-descriptions :column="2" label-placement="left" bordered>
        <n-descriptions-item :label="$t('profile.sourceFormatLabel')">
          {{ sourceFormatDisplay(profile.source_format ?? undefined) }}
        </n-descriptions-item>
        <n-descriptions-item :label="$t('profile.createdAt')">
          {{ fmtDate(profile.created_at) }}
        </n-descriptions-item>
      </n-descriptions>

      <n-divider />

      <template v-if="profile.academic_profile">
        <n-divider>{{ $t('profile.academicProfile') }}</n-divider>
        <n-input
          :value="profile.academic_profile"
          type="textarea"
          readonly
          :autosize="{ minRows: 8, maxRows: 20 }"
        />

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

      <ProfileChatPanel
        v-if="profileId"
        :profile-id="profileId"
        :visible="showChat"
        @profile-refreshed="refreshProfileSilent"
        style="margin-bottom: 16px"
      />

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
  </n-spin>
</template>

<style scoped>
.education-item,
.research-item,
.project-item {
  margin-bottom: 16px;
}
</style>
