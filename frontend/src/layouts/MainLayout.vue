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
  NButton,
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
  LanguageOutline,
} from '@vicons/ionicons5'
import type { MenuOption } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useTaskStore } from '@/stores/tasks'
import { setLocale } from '@/i18n'
import TaskPanel from '@/components/TaskPanel.vue'
import TaskNotificationHost from '@/components/TaskNotificationHost.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const taskStore = useTaskStore()
const message = useMessage()
const { t, locale } = useI18n()

onMounted(() => {
  taskStore.restoreFromServer()
})

// Menu options
const menuOptions = computed<MenuOption[]>(() => {
  const options: MenuOption[] = [
    {
      label: t('nav.profiles'),
      key: 'profile',
      icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) }),
    },
    {
      label: t('nav.professors'),
      key: 'professor',
      icon: () => h(NIcon, null, { default: () => h(PeopleOutline) }),
    },
    {
      label: t('nav.match'),
      key: 'match',
      icon: () => h(NIcon, null, { default: () => h(GitCompareOutline) }),
    },
    {
      label: t('nav.letters'),
      key: 'letter',
      icon: () => h(NIcon, null, { default: () => h(MailOutline) }),
    },
    {
      label: t('nav.settings'),
      key: 'settings',
      icon: () => h(NIcon, null, { default: () => h(SettingsOutline) }),
    },
  ]

  if (authStore.isAdmin) {
    options.push({
      label: t('nav.admin'),
      key: 'admin/users',
      icon: () => h(NIcon, null, { default: () => h(PeopleCircleOutline) }),
    })
  }

  return options
})

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

function handleMenuClick(key: string) {
  router.push(`/${key}`)
}

const userOptions = computed(() => [
  {
    label: t('nav.settings'),
    key: 'settings',
    icon: () => h(NIcon, null, { default: () => h(SettingsOutline) }),
  },
  {
    type: 'divider' as const,
    key: 'd1',
  },
  {
    label: t('nav.logout'),
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogOutOutline) }),
  },
])

function handleUserAction(key: string) {
  if (key === 'settings') {
    router.push('/settings')
  } else if (key === 'logout') {
    taskStore.reset()
    authStore.logout()
    message.success(t('nav.loggedOut'))
    router.push('/login')
  }
}

function toggleLang() {
  setLocale(locale.value === 'zh' ? 'en' : 'zh')
}
</script>

<template>
  <n-layout has-sider style="height: 100vh">
    <TaskNotificationHost />
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
      <n-layout-header bordered style="height: 60px; padding: 0 24px;">
        <n-space justify="end" align="center" style="height: 100%">
          <n-button text @click="toggleLang">
            <template #icon>
              <n-icon><LanguageOutline /></n-icon>
            </template>
            {{ locale === 'zh' ? 'EN' : '中' }}
          </n-button>
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
              <span>{{ authStore.user?.username || t('auth.username') }}</span>
            </n-space>
          </n-dropdown>
        </n-space>
      </n-layout-header>

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
