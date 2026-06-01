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
  useMessage,
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '@/stores/settings'
import PasswordRequirementCheck from '@/components/PasswordRequirementCheck.vue'
import { useAuthStore } from '@/stores/auth'
import { useApiError } from '@/composables/useApiError'
import { useHelpDrawer } from '@/composables/useHelpDrawer'
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
  deepseek_api_key_masked: null,
  deepseek_base_url: 'https://api.deepseek.com/v1',
  request_delay: 3,
  auto_enrich_on_save_fetch_publication_details: true,
  auto_enrich_on_save_paper_summaries: true,
  auto_enrich_on_save_research_profile: true,
})

const apiKeyInput = ref('')
const baseUrlInput = ref('')
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

async function fetchSettings() {
  loading.value = true
  try {
    settings.value = await settingsStore.fetchSettings()
    baseUrlInput.value = settings.value.deepseek_base_url
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
      updateData.deepseek_api_key = apiKeyInput.value
    }
    if (baseUrlInput.value !== settings.value.deepseek_base_url) {
      updateData.deepseek_base_url = baseUrlInput.value
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
                <n-button
                  tag="a"
                  href="https://platform.deepseek.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  type="primary"
                  size="small"
                  style="margin-top: 12px"
                >
                  {{ t('help.openDeepSeekPlatform') }}
                </n-button>
              </n-collapse-item>
            </n-collapse>
            <n-form label-placement="left" label-width="100">
              <n-form-item :label="t('settings.currentApiKey')">
                <span style="color: var(--muted-foreground)">
                  {{ settings.deepseek_api_key_masked || t('common.noData') }}
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
              <n-form-item :label="t('settings.apiBaseUrl')">
                <n-input v-model:value="baseUrlInput" placeholder="API Base URL" />
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
  </div>
</template>

<style scoped>
.password-field {
  width: 100%;
}
</style>
