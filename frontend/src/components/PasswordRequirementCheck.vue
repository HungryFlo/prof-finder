<script setup lang="ts">
import { computed } from 'vue'
import { NText } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { usePasswordChecks } from '@/composables/usePasswordChecks'

const props = defineProps<{
  password: string
}>()

const { t } = useI18n()
const { passwordChecks } = usePasswordChecks(computed(() => props.password))
</script>

<template>
  <div v-if="props.password" class="password-requirements">
    <div class="requirements-title">{{ t('auth.passwordRequirements') }}</div>
    <div :class="['req-item', passwordChecks.minLength ? 'met' : 'unmet']">
      <span class="req-icon">{{ passwordChecks.minLength ? '✓' : '✗' }}</span>
      <n-text :type="passwordChecks.minLength ? 'success' : 'error'" depth="3">
        {{ t('auth.passwordMinLength') }}
      </n-text>
    </div>
    <div :class="['req-item', passwordChecks.maxLength ? 'met' : 'unmet']">
      <span class="req-icon">{{ passwordChecks.maxLength ? '✓' : '✗' }}</span>
      <n-text :type="passwordChecks.maxLength ? 'success' : 'error'" depth="3">
        {{ t('auth.passwordMaxLength') }}
      </n-text>
    </div>
  </div>
</template>

<style scoped>
.password-requirements {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: var(--muted);
  border-radius: 4px;
  border: 1px solid var(--border);
}

.requirements-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--foreground);
  margin-bottom: 4px;
}

.req-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  line-height: 1.8;
}

.req-icon {
  font-size: 14px;
  font-weight: bold;
}

.req-item.met .req-icon {
  color: oklch(0.62 0.17 145);
}

.req-item.unmet .req-icon {
  color: var(--destructive);
}
</style>
