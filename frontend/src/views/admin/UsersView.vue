<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
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
import type { User } from '@/types'

const message = useMessage()

// State
const loading = ref(false)
const users = ref<User[]>([])

// Reset password modal
const showResetModal = ref(false)
const resetLoading = ref(false)
const selectedUser = ref<User | null>(null)
const newPassword = ref('')

// Table columns
const columns: DataTableColumns<User> = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '用户名', key: 'username', width: 150 },
  {
    title: '角色',
    key: 'is_admin',
    width: 100,
    render(row) {
      return row.is_admin
        ? h(NTag, { type: 'warning', size: 'small' }, { default: () => '管理员' })
        : h(NTag, { type: 'default', size: 'small' }, { default: () => '普通用户' })
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return new Date(row.created_at).toLocaleString('zh-CN')
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render(row) {
      return h(
        NButton,
        {
          size: 'small',
          onClick: () => openResetModal(row),
        },
        { default: () => '重置密码' }
      )
    },
  },
]

// Fetch users
async function fetchUsers() {
  loading.value = true
  try {
    users.value = await adminApi.listUsers()
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// Open reset password modal
function openResetModal(user: User) {
  selectedUser.value = user
  newPassword.value = ''
  showResetModal.value = true
}

// Reset password
async function handleResetPassword() {
  if (!selectedUser.value) return
  
  if (newPassword.value.length < 6) {
    message.error('密码至少需要 6 个字符')
    return
  }

  resetLoading.value = true
  try {
    await adminApi.resetPassword(selectedUser.value.id, newPassword.value)
    message.success('密码重置成功')
    showResetModal.value = false
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || '重置密码失败')
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
    <n-card title="用户管理">
      <n-data-table
        :columns="columns"
        :data="users"
        :loading="loading"
        :row-key="(row: User) => row.id"
      />
    </n-card>

    <!-- Reset Password Modal -->
    <n-modal
      v-model:show="showResetModal"
      preset="dialog"
      title="重置密码"
      positive-text="确认重置"
      negative-text="取消"
      :positive-button-props="{ loading: resetLoading }"
      @positive-click="handleResetPassword"
      style="width: 400px"
    >
      <p>为用户 <strong>{{ selectedUser?.username }}</strong> 设置新密码：</p>
      <n-form-item label="新密码">
        <n-input
          v-model:value="newPassword"
          type="password"
          placeholder="请输入新密码（至少6位）"
          show-password-on="click"
        />
      </n-form-item>
    </n-modal>
  </div>
</template>
