<script setup lang="ts">
import { h, computed, onMounted, ref, watch } from 'vue'
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
  NAlert,
  useMessage,
} from 'naive-ui'
import {
  DocumentTextOutline,
  PeopleOutline,
  GitCompareOutline,
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
import { settingsApi } from '@/api/settings'
import TaskPanel from '@/components/TaskPanel.vue'
import TaskNotificationHost from '@/components/TaskNotificationHost.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const taskStore = useTaskStore()
const message = useMessage()
const { t, locale } = useI18n()
const needsApiConfig = ref(false)

onMounted(() => {
  taskStore.restoreFromServer()
  checkApiConfiguration()
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
  if (path.startsWith('/settings')) return 'settings'
  if (path.startsWith('/admin')) return 'admin/users'
  return ''
})

const showApiConfigBanner = computed(() => needsApiConfig.value && route.path !== '/settings')

watch(() => route.path, (newPath, oldPath) => {
  if (oldPath === '/settings' && newPath !== '/settings') {
    checkApiConfiguration()
  }
})

async function checkApiConfiguration() {
  try {
    const settings = await settingsApi.get()
    needsApiConfig.value = !settings.deepseek_api_key_masked
  } catch {
    // Settings errors are handled by pages that need them; avoid blocking layout startup.
  }
}

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
  <n-layout has-sider class="app-root-layout">
    <TaskNotificationHost />
    <a class="skip-link" href="#main-content">{{ t('nav.skipToContent') }}</a>
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      show-trigger
      class="app-sider"
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
        class="app-layout-scroll"
        content-style="padding: 28px 28px 36px;"
      >
        <main id="main-content" class="main-content-shell" tabindex="-1">
          <n-alert
            v-if="showApiConfigBanner"
            type="warning"
            :title="t('settings.firstRunApiKeyTitle')"
            style="margin-bottom: 20px"
          >
            <n-space vertical align="start">
              <span>{{ t('settings.firstRunApiKeyDescription') }}</span>
              <n-button size="small" type="primary" @click="router.push('/settings')">
                {{ t('settings.configureApiKey') }}
              </n-button>
            </n-space>
          </n-alert>
          <router-view />
        </main>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style scoped>
.app-root-layout {
  position: relative;
  min-height: 100dvh;
}

.app-sider {
  min-height: 100dvh;
}

.app-layout-scroll {
  min-height: calc(100dvh - 60px);
  overflow: auto;
}

.skip-link {
  position: fixed;
  left: 0.75rem;
  top: 0.75rem;
  z-index: 2000;
  padding: 0.45rem 0.85rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #fff;
  background: #2f6f8f;
  border-radius: 8px;
  text-decoration: none;
  transform: translateY(-120%);
  opacity: 0;
  pointer-events: none;
  transition:
    transform 0.22s ease,
    opacity 0.22s ease;
}

.skip-link:focus {
  outline: none;
}

.skip-link:focus-visible {
  transform: translateY(0);
  opacity: 1;
  pointer-events: auto;
  box-shadow: 0 0 0 3px oklch(0.72 0.09 235 / 0.45);
}

.main-content-shell {
  max-width: 1440px;
  margin-inline: auto;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--n-border-color);
}

.logo-text {
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.2;
  text-wrap: balance;
  color: var(--n-text-color);
}

:deep(.n-menu .n-menu-item-content) {
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.15s ease;
}

:deep(.n-menu .n-menu-item-content:hover) {
  transform: translateX(1px);
}

:deep(.n-menu .n-menu-item-content--selected) {
  font-weight: 600;
}

:deep(.n-button.n-button--text-type) {
  transition:
    color 0.2s ease,
    background-color 0.2s ease,
    transform 0.15s ease;
}

:deep(.n-button.n-button--text-type:active) {
  transform: translateY(1px);
}
</style>
