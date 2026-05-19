<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NCard,
  NDataTable,
  NTag,
  NButton,
  NModal,
  NFormItem,
  NInput,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { adminApi } from '@/api/auth'
import { useDateLocale } from '@/composables/useDateLocale'
import { useApiError } from '@/composables/useApiError'
import type { User } from '@/types'

const message = useMessage()
const { t } = useI18n()
const { handleApiError } = useApiError()

const dateLocale = useDateLocale()

const loading = ref(false)
const users = ref<User[]>([])

const showResetModal = ref(false)
const resetLoading = ref(false)
const selectedUser = ref<User | null>(null)
const newPassword = ref('')

const columns = computed<DataTableColumns<User>>(() => [
  { title: t('admin.idColumn'), key: 'id', width: 80 },
  { title: t('admin.username'), key: 'username', width: 150 },
  {
    title: t('admin.role'),
    key: 'is_admin',
    width: 118,
    render(row) {
      return row.is_admin
        ? h(NTag, { type: 'warning', size: 'small' }, { default: () => t('admin.admin') })
        : h(NTag, { type: 'default', size: 'small' }, { default: () => t('admin.user') })
    },
  },
  {
    title: t('admin.createdAt'),
    key: 'created_at',
    width: 180,
    render(row) {
      return new Date(row.created_at).toLocaleString(dateLocale.value)
    },
  },
  {
    title: t('admin.actions'),
    key: 'actions',
    width: 200,
    render(row) {
      return h(
        NButton,
        {
          size: 'small',
          onClick: () => openResetModal(row),
        },
        { default: () => t('admin.resetPassword') }
      )
    },
  },
])

async function fetchUsers() {
  loading.value = true
  try {
    users.value = await adminApi.listUsers()
  } catch (error: unknown) {
    handleApiError(error, t('admin.fetchListFailed'))
  } finally {
    loading.value = false
  }
}

function openResetModal(user: User) {
  selectedUser.value = user
  newPassword.value = ''
  showResetModal.value = true
}

async function handleResetPassword() {
  if (!selectedUser.value) return

  if (newPassword.value.length < 6) {
    message.error(t('admin.passwordTooShort'))
    return
  }

  resetLoading.value = true
  try {
    await adminApi.resetPassword(selectedUser.value.id, newPassword.value)
    message.success(t('admin.resetSuccess'))
    showResetModal.value = false
  } catch (error: unknown) {
    handleApiError(error, t('admin.resetPasswordFail'))
  } finally {
    resetLoading.value = false
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div>
    <n-card :title="$t('admin.title')">
      <n-data-table
        :columns="columns"
        :data="users"
        :loading="loading"
        :row-key="(row: User) => row.id"
        :scroll-x="820"
      />
    </n-card>

    <n-modal
      v-model:show="showResetModal"
      preset="dialog"
      :title="$t('admin.resetPassword')"
      :positive-text="$t('admin.confirmResetPwd')"
      :negative-text="$t('common.cancel')"
      :positive-button-props="{ loading: resetLoading }"
      @positive-click="handleResetPassword"
      style="width: 400px"
    >
      <p>{{ $t('admin.resetPwdIntro', { username: selectedUser?.username ?? '' }) }}</p>
      <n-form-item :label="t('auth.newPassword')">
        <n-input
          v-model:value="newPassword"
          type="password"
          :placeholder="$t('admin.newPasswordPlaceholder')"
          show-password-on="click"
        />
      </n-form-item>
    </n-modal>
  </div>
</template>
