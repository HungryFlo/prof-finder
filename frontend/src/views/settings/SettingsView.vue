<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NCard,
  NForm,
  NFormItem,
  NGrid,
  NGi,
  NInput,
  NInputNumber,
  NButton,
  NSpace,
  NSwitch,
  NAlert,
  NCollapse,
  NCollapseItem,
  NList,
  NListItem,
  NTag,
  NEmpty,
  NPopconfirm,
  NSpin,
  NModal,
  NDynamicTags,
  NSelect,
  useMessage,
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '@/stores/settings'
import PasswordRequirementCheck from '@/components/PasswordRequirementCheck.vue'
import { useAuthStore } from '@/stores/auth'
import { useApiError } from '@/composables/useApiError'
import { useHelpDrawer } from '@/composables/useHelpDrawer'
import { universitiesApi } from '@/api/universities'
import type { University } from '@/api/universities'
import type { UserSettings } from '@/types'

const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const message = useMessage()
const { t } = useI18n()
const { handleApiError } = useApiError()
const { openHelp } = useHelpDrawer()

const loading = ref(false)
const saving = ref(false)
const settings = ref<UserSettings>({
  llm_provider: 'openai',
  llm_api_key_masked: null,
  llm_base_url: 'https://api.deepseek.com/v1',
  llm_model: 'deepseek-chat',
  request_delay: 3,
  auto_enrich_on_save_fetch_publication_details: true,
  auto_enrich_on_save_paper_summaries: true,
  auto_enrich_on_save_research_profile: true,
})

const providerOptions = [
  { label: 'OpenAI-compatible', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
]

const apiKeyInput = ref('')
const providerInput = ref<'openai' | 'anthropic'>('openai')
const baseUrlInput = ref('')
const modelInput = ref('')
const delayInput = ref(3)
const enrichFetch = ref(true)
const enrichSummaries = ref(true)
const enrichProfile = ref(true)

const passwordLoading = ref(false)
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

// University management
const universities = ref<University[]>([])
const universitiesLoading = ref(false)
const showAddUniversityModal = ref(false)
const addUniversityLoading = ref(false)
const newUniversityName = ref('')
const editingVariants = ref<{ id: number; variants: string[] } | null>(null)

async function fetchUniversities() {
  universitiesLoading.value = true
  try {
    universities.value = await universitiesApi.list()
  } catch {
    // silent
  } finally {
    universitiesLoading.value = false
  }
}

async function handleAddUniversity(): Promise<boolean> {
  if (!newUniversityName.value.trim()) {
    message.warning(t('university.fullNameRequired'))
    return false
  }
  addUniversityLoading.value = true
  try {
    const uni = await universitiesApi.create({ full_name: newUniversityName.value.trim() })
    universities.value.unshift(uni)
    newUniversityName.value = ''
    message.success(t('university.addSuccess'))
    return true
  } catch (error: unknown) {
    handleApiError(error, t('university.addFailed'))
    return false
  } finally {
    addUniversityLoading.value = false
  }
}

function resetAddUniversityModal() {
  newUniversityName.value = ''
}

async function handleDeleteUniversity(id: number) {
  try {
    await universitiesApi.delete(id)
    universities.value = universities.value.filter((u) => u.id !== id)
    message.success(t('university.deleteSuccess'))
  } catch (error: unknown) {
    handleApiError(error, t('university.deleteFailed'))
  }
}

function startEditVariants(uni: University) {
  editingVariants.value = { id: uni.id, variants: [...(uni.name_variants || [])] }
}

async function saveVariants() {
  if (!editingVariants.value) return
  try {
    const updated = await universitiesApi.update(editingVariants.value.id, {
      name_variants: editingVariants.value.variants,
    })
    const idx = universities.value.findIndex((u) => u.id === updated.id)
    if (idx >= 0) universities.value[idx] = updated
    editingVariants.value = null
    message.success(t('university.updateSuccess'))
  } catch (error: unknown) {
    handleApiError(error, t('university.updateFailed'))
  }
}

async function fetchSettings() {
  loading.value = true
  try {
    settings.value = await settingsStore.fetchSettings()
    providerInput.value = settings.value.llm_provider
    baseUrlInput.value = settings.value.llm_base_url
    modelInput.value = settings.value.llm_model
    delayInput.value = settings.value.request_delay
    enrichFetch.value = settings.value.auto_enrich_on_save_fetch_publication_details !== false
    enrichSummaries.value = settings.value.auto_enrich_on_save_paper_summaries !== false
    enrichProfile.value = settings.value.auto_enrich_on_save_research_profile !== false
  } catch (error: unknown) {
    handleApiError(error, t('settings.saveFailed'))
  } finally {
    loading.value = false
  }
}

async function handleSaveSettings() {
  saving.value = true
  try {
    const updateData: Record<string, string | number | boolean> = {}

    if (apiKeyInput.value) {
      updateData.llm_api_key = apiKeyInput.value
    }
    if (providerInput.value !== settings.value.llm_provider) {
      updateData.llm_provider = providerInput.value
    }
    if (baseUrlInput.value !== settings.value.llm_base_url) {
      updateData.llm_base_url = baseUrlInput.value
    }
    if (modelInput.value !== settings.value.llm_model) {
      updateData.llm_model = modelInput.value
    }
    if (delayInput.value !== settings.value.request_delay) {
      updateData.request_delay = delayInput.value
    }
    if (enrichFetch.value !== (settings.value.auto_enrich_on_save_fetch_publication_details !== false)) {
      updateData.auto_enrich_on_save_fetch_publication_details = enrichFetch.value
    }
    if (enrichSummaries.value !== (settings.value.auto_enrich_on_save_paper_summaries !== false)) {
      updateData.auto_enrich_on_save_paper_summaries = enrichSummaries.value
    }
    if (enrichProfile.value !== (settings.value.auto_enrich_on_save_research_profile !== false)) {
      updateData.auto_enrich_on_save_research_profile = enrichProfile.value
    }

    settings.value = await settingsStore.updateSettings(updateData)
    apiKeyInput.value = ''
    enrichFetch.value = settings.value.auto_enrich_on_save_fetch_publication_details !== false
    enrichSummaries.value = settings.value.auto_enrich_on_save_paper_summaries !== false
    enrichProfile.value = settings.value.auto_enrich_on_save_research_profile !== false
    message.success(t('settings.saveSuccess'))
  } catch (error: unknown) {
    handleApiError(error, t('settings.saveFailed'))
  } finally {
    saving.value = false
  }
}

async function handleChangePassword() {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    message.error(t('auth.passwordMismatch'))
    return
  }

  if (passwordForm.value.newPassword.length < 6) {
    message.error(t('auth.passwordMinLength'))
    return
  }

  passwordLoading.value = true
  try {
    await authStore.changePassword(
      passwordForm.value.currentPassword,
      passwordForm.value.newPassword
    )
    message.success(t('auth.changeSuccess'))
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    }
  } catch (error: unknown) {
    handleApiError(error, t('auth.changeFailed'))
  } finally {
    passwordLoading.value = false
  }
}

onMounted(() => {
  fetchSettings()
  fetchUniversities()
})
</script>

<template>
  <div>
    <n-space vertical :size="24">
      <n-grid cols="2" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
        <n-gi span="2 m:1">
          <n-card :title="t('settings.apiConfig')">
            <n-alert type="info" style="margin-bottom: 16px">
              {{ t('help.settingsApiKeyHint') }}
              <n-button text type="primary" size="small" style="margin-left: 4px" @click="openHelp">
                {{ t('help.settingsApiKeyLink') }}
              </n-button>
            </n-alert>
            <n-collapse style="margin-bottom: 16px">
              <n-collapse-item :title="t('help.apiKeyGuide')" name="apiKey">
                <ol style="margin: 0; padding-left: 20px; line-height: 1.6">
                  <li>{{ t('help.apiKeyStep1') }}</li>
                  <li>{{ t('help.apiKeyStep2') }}</li>
                  <li>{{ t('help.apiKeyStep3') }}</li>
                  <li>{{ t('help.apiKeyStep4') }}</li>
                  <li>{{ t('help.apiKeyStep5') }}</li>
                </ol>
                <p style="margin-top: 12px; color: var(--muted-foreground); font-size: 13px">
                  {{ t('settings.llmProviderExamples') }}
                </p>
              </n-collapse-item>
            </n-collapse>
            <n-form label-placement="left" label-width="100">
              <n-form-item :label="t('settings.llmProvider')">
                <n-select v-model:value="providerInput" :options="providerOptions" />
              </n-form-item>
              <n-form-item :label="t('settings.currentApiKey')">
                <span style="color: var(--muted-foreground)">
                  {{ settings.llm_api_key_masked || t('common.noData') }}
                </span>
              </n-form-item>
              <n-form-item :label="t('settings.newApiKey')">
                <n-input
                  v-model:value="apiKeyInput"
                  placeholder="sk-..."
                  type="password"
                  show-password-on="click"
                />
              </n-form-item>
              <n-form-item :label="t('settings.llmModel')">
                <n-input
                  v-model:value="modelInput"
                  :placeholder="t('settings.llmModelPlaceholder')"
                />
              </n-form-item>
              <n-form-item :label="t('settings.apiBaseUrl')">
                <n-input v-model:value="baseUrlInput" placeholder="https://api.example.com/v1" />
              </n-form-item>
              <n-form-item :label="t('settings.requestDelay')">
                <n-input-number v-model:value="delayInput" :min="1" :max="60" />
              </n-form-item>
              <n-form-item>
                <n-button type="primary" :loading="saving" @click="handleSaveSettings">
                  {{ t('settings.saveSettings') }}
                </n-button>
              </n-form-item>
            </n-form>
          </n-card>
        </n-gi>

        <n-gi span="2 m:1">
          <n-card :title="t('settings.professorAutoEnrich')">
            <n-form label-placement="left" label-width="180">
              <n-form-item :label="t('settings.autoEnrichFetchPublications')">
                <n-switch v-model:value="enrichFetch" />
              </n-form-item>
              <n-form-item :label="t('settings.autoEnrichPaperSummaries')">
                <n-switch v-model:value="enrichSummaries" />
              </n-form-item>
              <n-form-item :label="t('settings.autoEnrichResearchProfile')">
                <n-switch v-model:value="enrichProfile" />
              </n-form-item>
              <n-form-item>
                <n-button type="primary" :loading="saving" @click="handleSaveSettings">
                  {{ t('settings.saveSettings') }}
                </n-button>
              </n-form-item>
            </n-form>
          </n-card>
        </n-gi>
      </n-grid>

      <n-card :title="t('settings.universityManagement')">
        <template #header-extra>
          <n-button type="primary" size="small" @click="showAddUniversityModal = true">
            {{ t('university.add') }}
          </n-button>
        </template>
        <n-spin :show="universitiesLoading">
          <n-list v-if="universities.length" bordered>
            <n-list-item v-for="uni in universities" :key="uni.id">
              <n-space vertical style="width: 100%">
                <div style="display: flex; align-items: center; justify-content: space-between">
                  <strong>{{ uni.full_name }}</strong>
                  <n-space size="small">
                    <n-button size="tiny" @click="startEditVariants(uni)">
                      {{ t('professor.edit') }}
                    </n-button>
                    <n-popconfirm @positive-click="handleDeleteUniversity(uni.id)">
                      <template #trigger>
                        <n-button size="tiny" type="error">{{ t('professor.delete') }}</n-button>
                      </template>
                      {{ t('university.deleteConfirm') }}
                    </n-popconfirm>
                  </n-space>
                </div>
                <div v-if="editingVariants?.id === uni.id" style="margin-top: 8px">
                  <n-form-item :label="t('university.nameVariants')" label-placement="top">
                    <n-dynamic-tags v-model:value="editingVariants.variants" />
                  </n-form-item>
                  <n-space>
                    <n-button size="small" type="primary" @click="saveVariants">
                      {{ t('professor.save') }}
                    </n-button>
                    <n-button size="small" @click="editingVariants = null">
                      {{ t('common.cancel') }}
                    </n-button>
                  </n-space>
                </div>
                <div v-else>
                  <n-space v-if="uni.name_variants?.length" size="small" wrap>
                    <n-tag v-for="v in uni.name_variants" :key="v" size="small" type="info">
                      {{ v }}
                    </n-tag>
                  </n-space>
                  <span v-else style="color: var(--muted-foreground); font-size: 12px">
                    {{ t('university.nameVariantsDesc') }}
                  </span>
                </div>
              </n-space>
            </n-list-item>
          </n-list>
          <n-empty v-else :description="t('university.noUniversities')" />
        </n-spin>
      </n-card>

      <n-card :title="t('settings.changePassword')">
        <n-form label-placement="left" label-width="120">
          <n-form-item :label="t('auth.currentPassword')">
            <n-input
              v-model:value="passwordForm.currentPassword"
              type="password"
              :placeholder="t('auth.currentPasswordPlaceholder')"
              show-password-on="click"
            />
          </n-form-item>
          <n-form-item :label="t('auth.newPassword')">
            <div class="password-field">
              <n-input
                v-model:value="passwordForm.newPassword"
                type="password"
                :placeholder="t('auth.newPasswordPlaceholder')"
                show-password-on="click"
              />
              <PasswordRequirementCheck :password="passwordForm.newPassword" />
            </div>
          </n-form-item>
          <n-form-item :label="t('auth.confirmNewPasswordLabel')">
            <n-input
              v-model:value="passwordForm.confirmPassword"
              type="password"
              :placeholder="t('auth.confirmNewPasswordPlaceholder')"
              show-password-on="click"
            />
          </n-form-item>
          <n-form-item>
            <n-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
              {{ t('settings.changePassword') }}
            </n-button>
          </n-form-item>
        </n-form>
      </n-card>
    </n-space>

    <n-modal
      v-model:show="showAddUniversityModal"
      preset="dialog"
      :title="t('university.add')"
      :positive-text="t('university.add')"
      :negative-text="t('common.cancel')"
      :positive-button-props="{ loading: addUniversityLoading }"
      @positive-click="handleAddUniversity"
      @after-leave="resetAddUniversityModal"
      style="width: 480px"
    >
      <n-form-item :label="t('university.fullName')" label-placement="top">
        <n-input
          v-model:value="newUniversityName"
          :placeholder="t('university.fullNamePlaceholder')"
        />
      </n-form-item>
      <p style="color: var(--muted-foreground); font-size: 12px; margin: 0">
        {{ t('university.generatingVariants') }}
      </p>
    </n-modal>
  </div>
</template>

<style scoped>
.password-field {
  width: 100%;
}
</style>
