<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NSpace,
  NAlert,
  useMessage,
} from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()
const { t } = useI18n()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const formData = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const rules: FormRules = {
  currentPassword: [
    { required: true, message: () => t('auth.currentPasswordPlaceholder'), trigger: 'blur' },
  ],
  newPassword: [
    { required: true, message: () => t('auth.newPasswordPlaceholder'), trigger: 'blur' },
    { min: 6, message: () => t('auth.newPasswordPlaceholder'), trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: () => t('auth.confirmPasswordPlaceholder'), trigger: 'blur' },
    {
      validator: (_rule, value) => {
        if (value !== formData.value.newPassword) {
          return new Error(t('auth.passwordMismatch'))
        }
        return true
      },
      trigger: 'blur',
    },
  ],
}

async function handleChangePassword() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await authStore.changePassword(formData.value.currentPassword, formData.value.newPassword)
    message.success(t('auth.changeSuccess'))
    router.push('/')
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || t('auth.changeFailed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="change-password-container">
    <n-card :title="t('auth.changePasswordTitle')" style="width: 400px">
      <n-alert type="warning" style="margin-bottom: 16px">
        {{ t('auth.changePasswordHint') }}
      </n-alert>

      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="80"
      >
        <n-form-item :label="t('auth.currentPassword')" path="currentPassword">
          <n-input
            v-model:value="formData.currentPassword"
            type="password"
            :placeholder="t('auth.currentPasswordPlaceholder')"
            show-password-on="click"
          />
        </n-form-item>
        <n-form-item :label="t('auth.newPassword')" path="newPassword">
          <n-input
            v-model:value="formData.newPassword"
            type="password"
            :placeholder="t('auth.newPasswordPlaceholder')"
            show-password-on="click"
          />
        </n-form-item>
        <n-form-item :label="t('auth.confirmPassword')" path="confirmPassword">
          <n-input
            v-model:value="formData.confirmPassword"
            type="password"
            :placeholder="t('auth.confirmPasswordPlaceholder')"
            show-password-on="click"
            @keyup.enter="handleChangePassword"
          />
        </n-form-item>
      </n-form>

      <n-space vertical :size="12">
        <n-button
          type="primary"
          block
          :loading="loading"
          @click="handleChangePassword"
        >
          {{ t('common.confirm') }}
        </n-button>
      </n-space>
    </n-card>
  </div>
</template>

<style scoped>
.change-password-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
}
</style>
