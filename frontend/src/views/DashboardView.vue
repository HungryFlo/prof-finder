<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NGrid,
  NGi,
  NCard,
  NStatistic,
  NButton,
  NSpace,
  NIcon,
  NSpin,
  NList,
  NListItem,
  NThing,
  NTag,
  NSkeleton,
} from 'naive-ui'
import {
  DocumentTextOutline,
  PeopleOutline,
  GitCompareOutline,
  MailOutline,
  AddOutline,
  PersonAddOutline,
  PlayOutline,
  HomeOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { dashboardApi, type DashboardData } from '@/api/dashboard'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

const loading = ref(true)
const data = ref<DashboardData | null>(null)

const quote = computed(() => {
  const quotes = t('dashboard.quotes')
  if (Array.isArray(quotes) && quotes.length > 0) {
    return quotes[Math.floor(Math.random() * quotes.length)]
  }
  return ''
})

const username = computed(() => authStore.user?.username ?? '')

onMounted(async () => {
  try {
    data.value = await dashboardApi.getData()
  } catch {
    // Silently handle errors; stats will show as 0
  } finally {
    loading.value = false
  }
})

function navigateTo(path: string) {
  router.push(path)
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString()
}
</script>

<template>
  <div class="dashboard">
    <!-- Welcome Section -->
    <div class="welcome-section">
      <h1 class="welcome-title">
        <n-icon :size="28" style="margin-right: 8px; vertical-align: middle;">
          <HomeOutline />
        </n-icon>
        {{ t('dashboard.welcome', { username }) }}
      </h1>
      <p class="welcome-quote">{{ quote }}</p>
    </div>

    <!-- Statistics Cards -->
    <h2 class="section-title">{{ t('dashboard.statsTitle') }}</h2>
    <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
      <n-gi span="4 m:1">
        <n-card hoverable class="stat-card" @click="navigateTo('/profile')">
          <n-statistic :label="t('dashboard.profileCount')">
            <template #prefix>
              <n-icon :size="24" color="#18a058">
                <DocumentTextOutline />
              </n-icon>
            </template>
            <template #default>
              <n-spin v-if="loading" :size="18" />
              <span v-else>{{ data?.stats.profileCount ?? 0 }}</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 m:1">
        <n-card hoverable class="stat-card" @click="navigateTo('/professor')">
          <n-statistic :label="t('dashboard.professorCount')">
            <template #prefix>
              <n-icon :size="24" color="#2080f0">
                <PeopleOutline />
              </n-icon>
            </template>
            <template #default>
              <n-spin v-if="loading" :size="18" />
              <span v-else>{{ data?.stats.professorCount ?? 0 }}</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 m:1">
        <n-card hoverable class="stat-card" @click="navigateTo('/match')">
          <n-statistic :label="t('dashboard.matchCount')">
            <template #prefix>
              <n-icon :size="24" color="#f0a020">
                <GitCompareOutline />
              </n-icon>
            </template>
            <template #default>
              <n-spin v-if="loading" :size="18" />
              <span v-else>{{ data?.stats.matchCount ?? 0 }}</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 m:1">
        <n-card hoverable class="stat-card" @click="navigateTo('/letter')">
          <n-statistic :label="t('dashboard.letterCount')">
            <template #prefix>
              <n-icon :size="24" color="#d03050">
                <MailOutline />
              </n-icon>
            </template>
            <template #default>
              <n-spin v-if="loading" :size="18" />
              <span v-else>{{ data?.stats.letterCount ?? 0 }}</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Quick Actions -->
    <h2 class="section-title">{{ t('dashboard.quickActions') }}</h2>
    <n-space>
      <n-button type="primary" @click="navigateTo('/profile')">
        <template #icon>
          <n-icon><AddOutline /></n-icon>
        </template>
        {{ t('dashboard.createProfile') }}
      </n-button>
      <n-button type="info" @click="navigateTo('/professor')">
        <template #icon>
          <n-icon><PersonAddOutline /></n-icon>
        </template>
        {{ t('dashboard.addProfessor') }}
      </n-button>
      <n-button type="warning" @click="navigateTo('/match')">
        <template #icon>
          <n-icon><PlayOutline /></n-icon>
        </template>
        {{ t('dashboard.runMatch') }}
      </n-button>
    </n-space>

    <!-- Recent Activity -->
    <h2 class="section-title">{{ t('dashboard.recentActivity') }}</h2>
    <n-grid :cols="2" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
      <n-gi span="2 m:1">
        <n-card :title="t('dashboard.recentProfiles')" class="activity-card">
          <template #header-extra>
            <n-button text type="primary" @click="navigateTo('/profile')">
              {{ t('dashboard.viewAll') }}
            </n-button>
          </template>
          <n-spin v-if="loading" :size="24" style="display: block; text-align: center; padding: 24px;" />
          <n-list v-else-if="data?.recentProfiles && data.recentProfiles.length > 0" hoverable clickable>
            <n-list-item
              v-for="profile in data.recentProfiles"
              :key="profile.id"
              @click="navigateTo(`/profile/${profile.id}`)"
            >
              <n-thing :title="profile.title">
                <template #description>
                  <n-space size="small">
                    <n-tag v-if="profile.is_active" type="success" size="small">
                      {{ t('profile.active') }}
                    </n-tag>
                    <n-tag v-else size="small">
                      {{ t('profile.inactive') }}
                    </n-tag>
                    <span style="font-size: 12px; color: #999;">
                      {{ formatDate(profile.updated_at) }}
                    </span>
                  </n-space>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
          <div v-else class="empty-state">
            {{ t('dashboard.noRecentProfiles') }}
          </div>
        </n-card>
      </n-gi>
      <n-gi span="2 m:1">
        <n-card :title="t('dashboard.recentProfessors')" class="activity-card">
          <template #header-extra>
            <n-button text type="primary" @click="navigateTo('/professor')">
              {{ t('dashboard.viewAll') }}
            </n-button>
          </template>
          <n-spin v-if="loading" :size="24" style="display: block; text-align: center; padding: 24px;" />
          <n-list v-else-if="data?.recentProfessors && data.recentProfessors.length > 0" hoverable clickable>
            <n-list-item
              v-for="prof in data.recentProfessors"
              :key="prof.id"
              @click="navigateTo(`/professor/${prof.id}`)"
            >
              <n-thing :title="prof.name">
                <template #description>
                  <n-space size="small">
                    <span v-if="prof.affiliation" style="font-size: 12px; color: #999;">
                      {{ prof.affiliation }}
                    </span>
                    <n-tag v-if="prof.h_index" size="small">
                      H: {{ prof.h_index }}
                    </n-tag>
                  </n-space>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
          <div v-else class="empty-state">
            {{ t('dashboard.noRecentProfessors') }}
          </div>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.welcome-section {
  margin-bottom: 32px;
}

.welcome-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 8px;
  line-height: 1.3;
}

.welcome-quote {
  font-size: 1rem;
  color: #666;
  margin: 0;
  font-style: italic;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 28px 0 16px;
}

.stat-card {
  cursor: pointer;
  transition: box-shadow 0.2s ease, transform 0.15s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.activity-card {
  min-height: 300px;
}

.empty-state {
  text-align: center;
  padding: 32px 0;
  color: #999;
}
</style>
