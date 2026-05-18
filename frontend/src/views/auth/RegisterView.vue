<script setup lang="ts">
import { ref } from 'vue'
import { useApiError } from '@/composables/useApiError'
import { useRouter } from 'vue-router'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NSpace,
  useMessage,
} from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import PasswordRequirementCheck from '@/components/PasswordRequirementCheck.vue'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()
const { t } = useI18n()
const { handleApiError } = useApiError()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const formData = ref({
  username: '',
  password: '',
  confirmPassword: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: () => t('auth.usernamePlaceholder'), trigger: 'blur' },
    { min: 2, max: 50, message: '2-50 characters', trigger: 'blur' },
  ],
  password: [
    { required: true, message: () => t('auth.passwordPlaceholder'), trigger: 'blur' },
    {
      validator: (_rule, value: string) => {
        if (!value) return true
        if (value.length < 6) return new Error(t('auth.passwordMinLength'))
        if (value.length > 100) return new Error(t('auth.passwordMaxLength'))
        return true
      },
      trigger: 'input',
    },
  ],
  confirmPassword: [
    { required: true, message: () => t('auth.confirmPasswordPlaceholder'), trigger: 'blur' },
    {
      validator: (_rule, value) => {
        if (value !== formData.value.password) {
          return new Error(t('auth.passwordMismatch'))
        }
        return true
      },
      trigger: 'blur',
    },
  ],
}

async function handleRegister() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await authStore.register(formData.value.username, formData.value.password)
    message.success(t('auth.registerSuccess'))
    router.push('/login')
  } catch (error: unknown) {
    handleApiError(error, t('auth.registerFailed'))
  } finally {
    loading.value = false
  }
}

function goToLogin() {
  router.push('/login')
}
</script>

<template>
  <div class="register-container">
    <n-card :title="t('auth.registerTitle')" style="width: 400px">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="80"
      >
        <n-form-item :label="t('auth.username')" path="username">
          <n-input
            v-model:value="formData.username"
            :placeholder="t('auth.usernamePlaceholder')"
          />
        </n-form-item>
        <n-form-item :label="t('auth.password')" path="password">
          <div class="password-field">
            <n-input
              v-model:value="formData.password"
              type="password"
              :placeholder="t('auth.newPasswordPlaceholder')"
              show-password-on="click"
            />
            <PasswordRequirementCheck :password="formData.password" />
          </div>
        </n-form-item>
        <n-form-item :label="t('auth.confirmPassword')" path="confirmPassword">
          <n-input
            v-model:value="formData.confirmPassword"
            type="password"
            :placeholder="t('auth.confirmPasswordPlaceholder')"
            show-password-on="click"
            @keyup.enter="handleRegister"
          />
        </n-form-item>
      </n-form>

      <n-space vertical :size="12">
        <n-button
          type="primary"
          block
          :loading="loading"
          @click="handleRegister"
        >
          {{ t('auth.register') }}
        </n-button>
        <n-button block quaternary @click="goToLogin">
          {{ t('auth.hasAccount') }}
        </n-button>
      </n-space>
    </n-card>
  </div>
</template>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
}

.password-field {
  width: 100%;
}
</style>
