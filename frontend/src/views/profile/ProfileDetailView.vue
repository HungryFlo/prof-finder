<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
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

const loading = ref(false)
const saving = ref(false)
const showChat = ref(false)
const profile = ref<Profile | null>(null)
const profileId = ref(0)

// Editable form data
const formData = ref({
  title: '',
  name: '',
  skills: [] as string[],
  education: [] as EducationItem[],
  research_experience: [] as ResearchItem[],
  projects: [] as ProjectItem[],
})

async function fetchProfile() {
  const id = Number(route.params.id)
  if (!id) {
    message.error('无效的画像 ID')
    router.push('/profile')
    return
  }

  loading.value = true
  try {
    profile.value = await profilesApi.get(id)
    profileId.value = id
    // Initialize form data
    formData.value = {
      title: profile.value.title,
      name: profile.value.name || '',
      skills: [...(profile.value.skills || [])],
      education: [...(profile.value.education || [])],
      research_experience: [...(profile.value.research_experience || [])],
      projects: [...(profile.value.projects || [])],
    }
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '获取画像详情失败')
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
    // silent — don't disturb the chat flow
  }
}

async function handleSave() {
  if (!profile.value) return

  saving.value = true
  try {
    await profilesApi.update(profile.value.id, {
      title: formData.value.title,
      name: formData.value.name || undefined,
      skills: formData.value.skills,
      education: formData.value.education,
      research_experience: formData.value.research_experience,
      projects: formData.value.projects,
    })
    message.success('保存成功')
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '保存失败')
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
            <n-tag v-if="profile.is_active" type="success">已激活</n-tag>
            <n-tag v-else type="default">未激活</n-tag>
          </n-space>
        </n-space>
      </template>

      <template #header-extra>
        <n-space>
          <n-button @click="goBack">返回</n-button>
          <n-button
            v-if="profile.academic_profile"
            :type="showChat ? 'default' : 'info'"
            @click="showChat = !showChat"
          >
            {{ showChat ? '收起 AI' : 'AI 优化' }}
          </n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">保存</n-button>
        </n-space>
      </template>

      <n-descriptions :column="2" label-placement="left" bordered>
        <n-descriptions-item label="来源格式">
          {{ profile.source_format || '手动输入' }}
        </n-descriptions-item>
        <n-descriptions-item label="创建时间">
          {{ new Date(profile.created_at).toLocaleString('zh-CN') }}
        </n-descriptions-item>
      </n-descriptions>

      <n-divider />

      <template v-if="profile.academic_profile">
        <n-divider>学生学术画像</n-divider>
        <n-input
          :value="profile.academic_profile"
          type="textarea"
          readonly
          :autosize="{ minRows: 8, maxRows: 20 }"
        />

        <n-space v-if="profile.evidence_notes?.length" vertical style="margin-top: 16px">
          <strong>证据摘要</strong>
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
          <strong>冲突说明</strong>
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
        <n-form-item label="画像标题">
          <n-input v-model:value="formData.title" placeholder="画像标题" />
        </n-form-item>

        <n-form-item label="姓名">
          <n-input v-model:value="formData.name" placeholder="姓名" />
        </n-form-item>

        <n-form-item label="技能">
          <n-dynamic-tags v-model:value="formData.skills" />
        </n-form-item>

        <n-divider>教育经历</n-divider>
        <div v-for="(edu, index) in formData.education" :key="index" class="education-item">
          <n-space>
            <n-input v-model:value="edu.degree" placeholder="学位" style="width: 120px" />
            <n-input v-model:value="edu.school" placeholder="学校" style="width: 200px" />
            <n-input v-model:value="edu.major" placeholder="专业" style="width: 150px" />
            <n-input v-model:value="edu.period" placeholder="时间段" style="width: 150px" />
            <n-button
              size="small"
              type="error"
              @click="formData.education.splice(index, 1)"
            >
              删除
            </n-button>
          </n-space>
        </div>
        <n-button
          dashed
          @click="formData.education.push({ degree: '', school: '', major: '', period: '' })"
        >
          添加教育经历
        </n-button>

        <n-divider>研究经历</n-divider>
        <div v-for="(exp, index) in formData.research_experience" :key="index" class="research-item">
          <n-space vertical style="width: 100%">
            <n-space>
              <n-input v-model:value="exp.title" placeholder="职位/角色" style="width: 200px" />
              <n-input v-model:value="exp.organization" placeholder="机构" style="width: 200px" />
              <n-input v-model:value="exp.period" placeholder="时间段" style="width: 150px" />
              <n-button
                size="small"
                type="error"
                @click="formData.research_experience.splice(index, 1)"
              >
                删除
              </n-button>
            </n-space>
            <n-input
              v-model:value="exp.description"
              type="textarea"
              placeholder="描述"
              :rows="2"
            />
          </n-space>
        </div>
        <n-button
          dashed
          @click="formData.research_experience.push({ title: '', organization: '', description: '', period: '' })"
        >
          添加研究经历
        </n-button>

        <n-divider>项目经历</n-divider>
        <div v-for="(proj, index) in formData.projects" :key="index" class="project-item">
          <n-space vertical style="width: 100%">
            <n-space>
              <n-input v-model:value="proj.name" placeholder="项目名称" style="width: 300px" />
              <n-button
                size="small"
                type="error"
                @click="formData.projects.splice(index, 1)"
              >
                删除
              </n-button>
            </n-space>
            <n-input
              v-model:value="proj.description"
              type="textarea"
              placeholder="项目描述"
              :rows="2"
            />
          </n-space>
        </div>
        <n-button
          dashed
          @click="formData.projects.push({ name: '', description: '' })"
        >
          添加项目经历
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
