<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NAlert,
  NButton,
  NCard,
  NForm,
  NFormItem,
  NInput,
  NSpace,
  useMessage,
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { setupApi } from '@/api/setup'
import { useApiError } from '@/composables/useApiError'
import { useSetupGate } from '@/composables/useSetupGate'

const router = useRouter()
const message = useMessage()
const { t } = useI18n()
const { handleApiError } = useApiError()
const { ensureStatus, resetStatus } = useSetupGate()

const dataDir = ref('')
const loading = ref(false)
const browsing = ref(false)
const restarting = ref(false)

onMounted(async () => {
  const status = await ensureStatus()
  if (!status.packaged) {
    router.replace('/login')
    return
  }
  if (status.configured) {
    router.replace('/login')
    return
  }
  if (status.suggested_data_dir) {
    dataDir.value = status.suggested_data_dir
  }
})

async function handleBrowse() {
  browsing.value = true
  try {
    dataDir.value = await setupApi.pickDirectory()
  } catch (error: unknown) {
    handleApiError(error, t('setup.browseFailed'))
  } finally {
    browsing.value = false
  }
}

async function waitForConfigured(): Promise<void> {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 1000))
    resetStatus()
    const status = await setupApi.getStatus()
    if (status.configured) {
      return
    }
  }
  throw new Error('timeout')
}

async function handleComplete() {
  const trimmed = dataDir.value.trim()
  if (!trimmed) {
    message.warning(t('setup.pathRequired'))
    return
  }

  loading.value = true
  try {
    await setupApi.complete(trimmed)
    restarting.value = true
    message.success(t('setup.completeSuccess'))
    await waitForConfigured()
    router.replace('/login')
  } catch (error: unknown) {
    if (restarting.value) {
      try {
        await waitForConfigured()
        router.replace('/login')
        return
      } catch {
        message.error(t('setup.restartTimeout'))
        return
      }
    }
    handleApiError(error, t('setup.completeFailed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="setup-container">
    <n-card :title="t('setup.title')" style="max-width: 560px; width: 100%">
      <n-alert type="info" :title="t('setup.introTitle')" style="margin-bottom: 16px">
        {{ t('setup.introBody') }}
      </n-alert>

      <n-form label-placement="top">
        <n-form-item :label="t('setup.dataDirLabel')">
          <n-input
            v-model:value="dataDir"
            :placeholder="t('setup.dataDirPlaceholder')"
            :disabled="loading || restarting"
          />
        </n-form-item>
      </n-form>

      <p class="setup-hint">{{ t('setup.modelHint') }}</p>

      <n-space>
        <n-button :disabled="loading || restarting" :loading="browsing" @click="handleBrowse">
          {{ t('setup.browse') }}
        </n-button>
        <n-button
          type="primary"
          :loading="loading || restarting"
          :disabled="restarting"
          @click="handleComplete"
        >
          {{ restarting ? t('setup.restarting') : t('setup.complete') }}
        </n-button>
      </n-space>
    </n-card>
  </div>
</template>

<style scoped>
.setup-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background-color: var(--background);
}

.setup-hint {
  margin: 0 0 16px;
  color: var(--n-text-color-3);
  font-size: 13px;
}
</style>
