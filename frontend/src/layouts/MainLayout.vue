<script setup lang="ts">
import { h, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout,
  NLayoutHeader,
  NLayoutSider,
  NLayoutContent,
  NMenu,
  NDropdown,
  NAvatar,
  NSpace,
  NIcon,
  useMessage,
} from 'naive-ui'
import {
  DocumentTextOutline,
  PeopleOutline,
  GitCompareOutline,
  MailOutline,
  SettingsOutline,
  PeopleCircleOutline,
  LogOutOutline,
} from '@vicons/ionicons5'
import type { MenuOption } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { useTaskStore } from '@/stores/tasks'
import TaskPanel from '@/components/TaskPanel.vue'
import TaskNotificationHost from '@/components/TaskNotificationHost.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const taskStore = useTaskStore()
const message = useMessage()

onMounted(() => {
  taskStore.restoreFromServer()
})

// Menu options
const menuOptions = computed<MenuOption[]>(() => {
  const options: MenuOption[] = [
    {
      label: '学生画像',
      key: 'profile',
      icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) }),
    },
    {
      label: '教授管理',
      key: 'professor',
      icon: () => h(NIcon, null, { default: () => h(PeopleOutline) }),
    },
    {
      label: '匹配结果',
      key: 'match',
      icon: () => h(NIcon, null, { default: () => h(GitCompareOutline) }),
    },
    {
      label: '联络邮件',
      key: 'letter',
      icon: () => h(NIcon, null, { default: () => h(MailOutline) }),
    },
    {
      label: '设置',
      key: 'settings',
      icon: () => h(NIcon, null, { default: () => h(SettingsOutline) }),
    },
  ]

  // Add admin menu for admin users
  if (authStore.isAdmin) {
    options.push({
      label: '用户管理',
      key: 'admin/users',
      icon: () => h(NIcon, null, { default: () => h(PeopleCircleOutline) }),
    })
  }

  return options
})

// Current menu key based on route
const activeKey = computed(() => {
  const path = route.path
  if (path.startsWith('/profile')) return 'profile'
  if (path.startsWith('/professor')) return 'professor'
  if (path.startsWith('/match')) return 'match'
  if (path.startsWith('/letter')) return 'letter'
  if (path.startsWith('/settings')) return 'settings'
  if (path.startsWith('/admin')) return 'admin/users'
  return ''
})

// Handle menu click
function handleMenuClick(key: string) {
  router.push(`/${key}`)
}

// User dropdown options
const userOptions = [
  {
    label: '设置',
    key: 'settings',
    icon: () => h(NIcon, null, { default: () => h(SettingsOutline) }),
  },
  {
    type: 'divider',
    key: 'd1',
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogOutOutline) }),
  },
]

function handleUserAction(key: string) {
  if (key === 'settings') {
    router.push('/settings')
  } else if (key === 'logout') {
    authStore.logout()
    message.success('已退出登录')
    router.push('/login')
  }
}
</script>

<template>
  <n-layout has-sider style="height: 100vh">
    <TaskNotificationHost />
    <!-- Sidebar -->
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      show-trigger
      style="height: 100vh"
    >
      <div class="logo">
        <span class="logo-text">Prof-Finder</span>
      </div>
      <n-menu
        :options="menuOptions"
        :value="activeKey"
        @update:value="handleMenuClick"
      />
    </n-layout-sider>

    <n-layout>
      <!-- Header -->
      <n-layout-header bordered style="height: 60px; padding: 0 24px;">
        <n-space justify="end" align="center" style="height: 100%">
          <TaskPanel />
          <n-dropdown
            :options="userOptions"
            trigger="click"
            @select="handleUserAction"
          >
            <n-space align="center" style="cursor: pointer">
              <n-avatar round size="small">
                {{ authStore.user?.username?.[0]?.toUpperCase() || 'U' }}
              </n-avatar>
              <span>{{ authStore.user?.username || '用户' }}</span>
            </n-space>
          </n-dropdown>
        </n-space>
      </n-layout-header>

      <!-- Content -->
      <n-layout-content
        content-style="padding: 24px;"
        style="height: calc(100vh - 60px); overflow: auto;"
      >
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--n-border-color);
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--n-text-color);
}
</style>
