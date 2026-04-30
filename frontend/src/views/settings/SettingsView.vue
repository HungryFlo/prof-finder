<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NButton,
  NSpace,
  useMessage,
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { settingsApi } from '@/api/settings'
import { useAuthStore } from '@/stores/auth'
import type { UserSettings } from '@/types'

const authStore = useAuthStore()
const message = useMessage()
const { t } = useI18n()

const loading = ref(false)
const saving = ref(false)
const settings = ref<UserSettings>({
  deepseek_api_key_masked: null,
  deepseek_base_url: 'https://api.deepseek.com/v1',
  request_delay: 3,
})

const apiKeyInput = ref('')
const baseUrlInput = ref('')
const delayInput = ref(3)

const passwordLoading = ref(false)
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

async function fetchSettings() {
  loading.value = true
  try {
    settings.value = await settingsApi.get()
    baseUrlInput.value = settings.value.deepseek_base_url
    delayInput.value = settings.value.request_delay
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('settings.saveFailed'))
  } finally {
    loading.value = false
  }
}

async function handleSaveSettings() {
  saving.value = true
  try {
    const updateData: Record<string, string | number> = {}

    if (apiKeyInput.value) {
      updateData.deepseek_api_key = apiKeyInput.value
    }
    if (baseUrlInput.value !== settings.value.deepseek_base_url) {
      updateData.deepseek_base_url = baseUrlInput.value
    }
    if (delayInput.value !== settings.value.request_delay) {
      updateData.request_delay = delayInput.value
    }

    settings.value = await settingsApi.update(updateData)
    apiKeyInput.value = ''
    message.success(t('settings.saveSuccess'))
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('settings.saveFailed'))
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
    message.error(t('auth.passwordMismatch'))
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
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('auth.changeFailed'))
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
      <n-card :title="t('settings.apiConfig')">
        <n-form label-placement="left" label-width="120">
          <n-form-item :label="t('settings.currentApiKey')">
            <span style="color: #999">
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
            <n-input
              v-model:value="passwordForm.newPassword"
              type="password"
              :placeholder="t('auth.newPasswordPlaceholder')"
              show-password-on="click"
            />
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
