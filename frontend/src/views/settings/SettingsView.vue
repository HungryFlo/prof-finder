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
import { settingsApi } from '@/api/settings'
import { useAuthStore } from '@/stores/auth'
import type { UserSettings } from '@/types'

const authStore = useAuthStore()
const message = useMessage()

// Settings state
const loading = ref(false)
const saving = ref(false)
const settings = ref<UserSettings>({
  deepseek_api_key_masked: null,
  deepseek_base_url: 'https://api.deepseek.com/v1',
  request_delay: 3,
})

// Form for updates
const apiKeyInput = ref('')
const baseUrlInput = ref('')
const delayInput = ref(3)

// Password change
const passwordLoading = ref(false)
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

// Fetch settings
async function fetchSettings() {
  loading.value = true
  try {
    settings.value = await settingsApi.get()
    baseUrlInput.value = settings.value.deepseek_base_url
    delayInput.value = settings.value.request_delay
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '获取设置失败')
  } finally {
    loading.value = false
  }
}

// Save settings
async function handleSaveSettings() {
  saving.value = true
  try {
    const updateData: {
      deepseek_api_key?: string
      deepseek_base_url?: string
      request_delay?: number
    } = {}
    
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
    message.success('设置保存成功')
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// Change password
async function handleChangePassword() {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    message.error('两次输入的密码不一致')
    return
  }
  
  if (passwordForm.value.newPassword.length < 6) {
    message.error('新密码至少需要 6 个字符')
    return
  }

  passwordLoading.value = true
  try {
    await authStore.changePassword(
      passwordForm.value.currentPassword,
      passwordForm.value.newPassword
    )
    message.success('密码修改成功')
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    }
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '密码修改失败')
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
      <!-- API Settings -->
      <n-card title="API 配置">
        <n-form label-placement="left" label-width="120">
          <n-form-item label="当前 API Key">
            <span style="color: #999">
              {{ settings.deepseek_api_key_masked || '未配置' }}
            </span>
          </n-form-item>
          <n-form-item label="新 API Key">
            <n-input
              v-model:value="apiKeyInput"
              placeholder="输入新的 DeepSeek API Key（留空则不修改）"
              type="password"
              show-password-on="click"
            />
          </n-form-item>
          <n-form-item label="API Base URL">
            <n-input v-model:value="baseUrlInput" placeholder="API Base URL" />
          </n-form-item>
          <n-form-item label="爬虫延时">
            <n-input-number v-model:value="delayInput" :min="1" :max="60">
              <template #suffix>秒</template>
            </n-input-number>
          </n-form-item>
          <n-form-item>
            <n-button type="primary" :loading="saving" @click="handleSaveSettings">
              保存设置
            </n-button>
          </n-form-item>
        </n-form>
      </n-card>

      <!-- Password Change -->
      <n-card title="修改密码">
        <n-form label-placement="left" label-width="120">
          <n-form-item label="当前密码">
            <n-input
              v-model:value="passwordForm.currentPassword"
              type="password"
              placeholder="请输入当前密码"
              show-password-on="click"
            />
          </n-form-item>
          <n-form-item label="新密码">
            <n-input
              v-model:value="passwordForm.newPassword"
              type="password"
              placeholder="请输入新密码（至少6位）"
              show-password-on="click"
            />
          </n-form-item>
          <n-form-item label="确认新密码">
            <n-input
              v-model:value="passwordForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              show-password-on="click"
            />
          </n-form-item>
          <n-form-item>
            <n-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
              修改密码
            </n-button>
          </n-form-item>
        </n-form>
      </n-card>
    </n-space>
  </div>
</template>
