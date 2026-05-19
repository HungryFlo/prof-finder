<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
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
import { useApiError } from '@/composables/useApiError'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const message = useMessage()
const { t } = useI18n()
const { handleApiError } = useApiError()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const formData = ref({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: () => t('auth.usernamePlaceholder'), trigger: 'blur' },
  ],
  password: [
    { required: true, message: () => t('auth.passwordPlaceholder'), trigger: 'blur' },
  ],
}

async function handleLogin() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const response = await authStore.login(formData.value.username, formData.value.password)

    message.success(t('auth.loginSuccess'))

    if (response.must_change_password) {
      router.push('/change-password')
    } else {
      const redirect = route.query.redirect as string
      router.push(redirect || '/')
    }
  } catch (error: unknown) {
    handleApiError(error, t('auth.loginFailed'))
  } finally {
    loading.value = false
  }
}

function goToRegister() {
  router.push('/register')
}
</script>

<template>
  <div class="login-container">
    <n-card :title="t('auth.loginTitle')" style="width: 400px">
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
            @keyup.enter="handleLogin"
          />
        </n-form-item>
        <n-form-item :label="t('auth.password')" path="password">
          <n-input
            v-model:value="formData.password"
            type="password"
            :placeholder="t('auth.passwordPlaceholder')"
            show-password-on="click"
            @keyup.enter="handleLogin"
          />
        </n-form-item>
      </n-form>

      <n-space vertical :size="12">
        <n-button
          type="primary"
          block
          :loading="loading"
          @click="handleLogin"
        >
          {{ t('auth.login') }}
        </n-button>
        <n-button block quaternary @click="goToRegister">
          {{ t('auth.noAccount') }}
        </n-button>
      </n-space>
    </n-card>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--background);
}
</style>
