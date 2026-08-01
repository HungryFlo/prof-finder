<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { NIcon, NSpin, NButton, NResult, NTag } from 'naive-ui'
import {
  PersonOutline,
  SchoolOutline,
  GitCompareOutline,
  MailOutline,
  LayersOutline,
  ChevronForwardOutline,
  CheckmarkCircleOutline,
  EllipseOutline,
  SparklesOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { dashboardApi, type DashboardData } from '@/api/dashboard'
import { poolsApi } from '@/api/pools'
import { useApiError } from '@/composables/useApiError'
import { useFormatDate } from '@/composables/useDateLocale'
import { useHelpDrawer } from '@/composables/useHelpDrawer'

const router = useRouter()
const { t, tm } = useI18n()
const { formatRelativeTime } = useFormatDate()
const { handleApiError } = useApiError()
const authStore = useAuthStore()
const { openHelp } = useHelpDrawer()

const loading = ref(true)
const loadFailed = ref(false)
const data = ref<DashboardData | null>(null)
const poolStoryCount = ref(0)

const username = computed(() => authStore.user?.username ?? '')

const quotes = computed(() => tm('dashboard.quotes') as string[])

const dailyQuote = computed(() => {
  const list = quotes.value
  if (!list?.length) return ''
  const today = new Date()
  const seed = today.getFullYear() * 10000 + (today.getMonth() + 1) * 100 + today.getDate()
  return list[seed % list.length]
})

const steps = computed(() => [
  {
    key: 'pool',
    label: t('dashboard.stepPool'),
    desc: t('dashboard.stepPoolDesc'),
    done: poolStoryCount.value > 0,
    icon: LayersOutline,
    route: '/pool',
  },
  {
    key: 'profile',
    label: t('dashboard.stepProfile'),
    desc: t('dashboard.stepProfileDesc'),
    done: (data.value?.stats.profileCount ?? 0) > 0,
    icon: PersonOutline,
    route: '/profile',
  },
  {
    key: 'professors',
    label: t('dashboard.stepProfessors'),
    desc: t('dashboard.stepProfessorsDesc'),
    done: (data.value?.stats.professorCount ?? 0) > 0,
    icon: SchoolOutline,
    route: '/professor',
  },
  {
    key: 'match',
    label: t('dashboard.stepMatch'),
    desc: t('dashboard.stepMatchDesc'),
    done: (data.value?.stats.matchCount ?? 0) > 0,
    icon: GitCompareOutline,
    route: '/match',
  },
  {
    key: 'letters',
    label: t('dashboard.stepLetters'),
    desc: t('dashboard.stepLettersDesc'),
    done: (data.value?.stats.letterCount ?? 0) > 0,
    icon: MailOutline,
    route: '/letter',
  },
])

const activeStepIndex = computed(() => {
  const idx = steps.value.findIndex((s) => !s.done)
  return idx === -1 ? steps.value.length : idx
})

const topMatches = computed(() => data.value?.topMatches ?? [])
const recentProfiles = computed(() => data.value?.recentProfiles ?? [])
const recentProfessors = computed(() => data.value?.recentProfessors ?? [])
const recentLetters = computed(() => data.value?.recentLetters ?? [])

const activeProfile = computed(() => data.value?.activeProfile ?? null)

function navigateTo(path: string) {
  router.push(path)
}

function scoreColor(score: number): string {
  if (score >= 70) return 'var(--primary)'
  if (score >= 40) return 'oklch(0.7 0.14 85)'
  return 'var(--muted-foreground)'
}

async function loadDashboard() {
  loading.value = true
  loadFailed.value = false
  try {
    const [dash, pools] = await Promise.all([
      dashboardApi.getData(),
      poolsApi.list().catch(() => []),
    ])
    data.value = dash
    poolStoryCount.value = pools.reduce((sum, p) => sum + (p.story_count || 0), 0)
  } catch (error: unknown) {
    loadFailed.value = true
    handleApiError(error, t('dashboard.loadFailed'))
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="dashboard">
    <!-- Hero -->
    <header class="hero">
      <div class="hero-inner">
        <h1 class="hero-greeting">{{ t('dashboard.welcome', { username }) }}</h1>
        <p v-if="dailyQuote" class="hero-quote">{{ dailyQuote }}</p>
      </div>
    </header>

    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <n-spin :size="32" />
    </div>

    <div v-else-if="loadFailed" class="loading-state">
      <n-result status="error" :title="t('dashboard.loadFailed')">
        <template #footer>
          <n-button type="primary" @click="loadDashboard">{{ t('common.retry') }}</n-button>
        </template>
      </n-result>
    </div>

    <template v-else>
      <!-- Progress Flow -->
      <section class="flow-section">
        <div class="flow-section__header">
          <h2 class="section-heading">{{ t('dashboard.flowTitle') }}</h2>
          <n-button text type="primary" size="small" @click="openHelp">
            {{ t('help.viewGuide') }}
          </n-button>
        </div>
        <div class="flow-steps">
          <div
            v-for="(step, i) in steps"
            :key="step.key"
            class="flow-step"
            :class="{
              'flow-step--done': step.done,
              'flow-step--active': i === activeStepIndex,
            }"
            @click="navigateTo(step.route)"
          >
            <div class="flow-step__indicator">
              <div v-if="step.done" class="flow-step__check">
                <n-icon :size="20"><CheckmarkCircleOutline /></n-icon>
              </div>
              <div v-else-if="i === activeStepIndex" class="flow-step__pulse" />
              <div v-else class="flow-step__circle">
                <n-icon :size="16"><EllipseOutline /></n-icon>
              </div>
              <div v-if="i < steps.length - 1" class="flow-step__connector" :class="{ 'flow-step__connector--done': steps[i + 1]?.done }" />
            </div>
            <div class="flow-step__content">
              <span class="flow-step__label">{{ step.label }}</span>
              <span class="flow-step__desc">{{ step.desc }}</span>
            </div>
            <n-icon :size="16" class="flow-step__arrow"><ChevronForwardOutline /></n-icon>
          </div>
        </div>
      </section>

      <!-- Main Grid: Profile + Top Matches -->
      <div class="main-grid">
        <!-- Active Profile Card -->
        <section class="profile-card" @click="activeProfile ? navigateTo(`/profile/${activeProfile.id}`) : navigateTo('/profile')">
          <div class="profile-card__header">
            <h2 class="section-heading">{{ t('dashboard.yourProfile') }}</h2>
            <n-button v-if="!activeProfile" text type="primary" size="small" @click.stop="navigateTo('/profile')">
              {{ t('dashboard.createProfile') }}
            </n-button>
          </div>

          <template v-if="activeProfile">
            <div class="profile-card__title-row">
              <span class="profile-card__name">{{ activeProfile.title }}</span>
              <n-tag type="success" size="small" round>{{ t('dashboard.activeProfile') }}</n-tag>
            </div>
            <p class="profile-card__updated">{{ t('dashboard.lastUpdated', { date: formatRelativeTime(activeProfile.updated_at) }) }}</p>

            <div v-if="activeProfile.education?.length" class="profile-card__section">
              <span class="profile-card__section-label">{{ t('dashboard.profileEducation') }}</span>
              <div class="profile-card__edu-list">
                <div v-for="(edu, i) in activeProfile.education.slice(0, 3)" :key="i" class="profile-card__edu">
                  <span class="profile-card__edu-degree">{{ edu.degree }}</span>
                  <span class="profile-card__edu-school">{{ edu.school }}</span>
                </div>
              </div>
            </div>

            <div v-if="activeProfile.skills?.length" class="profile-card__section">
              <span class="profile-card__section-label">{{ t('dashboard.profileSkills') }}</span>
              <div class="profile-card__skills">
                <span v-for="skill in activeProfile.skills.slice(0, 8)" :key="skill" class="skill-chip">{{ skill }}</span>
                <span v-if="activeProfile.skills.length > 8" class="skill-chip skill-chip--more">+{{ activeProfile.skills.length - 8 }}</span>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="profile-card__empty">
              <n-icon :size="40" class="profile-card__empty-icon"><PersonOutline /></n-icon>
              <p>{{ t('dashboard.noRecentProfiles') }}</p>
            </div>
          </template>
        </section>

        <!-- Top Matches -->
        <section class="matches-card">
          <div class="matches-card__header">
            <h2 class="section-heading">{{ t('dashboard.topMatches') }}</h2>
            <n-button v-if="topMatches.length" text type="primary" size="small" @click="navigateTo('/match')">
              {{ t('dashboard.viewAll') }}
            </n-button>
          </div>
          <p class="matches-card__desc">{{ t('dashboard.topMatchesDesc') }}</p>

          <template v-if="topMatches.length">
            <div class="match-list">
              <div
                v-for="(match, i) in topMatches"
                :key="match.professor_id"
                class="match-item"
                @click="navigateTo(`/match?professor=${match.professor_id}`)"
              >
                <span class="match-item__rank">{{ i + 1 }}</span>
                <div class="match-item__info">
                  <span class="match-item__name">{{ match.professor_name }}</span>
                  <span v-if="match.professor_affiliation" class="match-item__affiliation">{{ match.professor_affiliation }}</span>
                </div>
                <div class="match-item__score-wrap">
                  <div class="match-item__bar-bg">
                    <div
                      class="match-item__bar"
                      :style="{ width: `${match.score}%`, backgroundColor: scoreColor(match.score) }"
                    />
                  </div>
                  <span class="match-item__score" :style="{ color: scoreColor(match.score) }">
                    {{ match.score.toFixed(1) }}%
                  </span>
                </div>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="matches-card__empty">
              <n-icon :size="40" class="matches-card__empty-icon"><SparklesOutline /></n-icon>
              <p>{{ t('dashboard.noMatchesYet') }}</p>
              <n-button type="primary" size="small" @click="navigateTo('/match')">
                {{ t('dashboard.runMatchCta') }}
              </n-button>
            </div>
          </template>
        </section>
      </div>

      <!-- Recent Activity -->
      <section class="activity-section">
        <h2 class="section-heading">{{ t('dashboard.recentActivity') }}</h2>
        <div class="activity-grid">
          <!-- Profiles -->
          <div class="activity-column">
            <div class="activity-column__header">
              <span class="activity-column__title">{{ t('dashboard.recentProfiles') }}</span>
              <n-button v-if="recentProfiles.length" text type="primary" size="tiny" @click="navigateTo('/profile')">
                {{ t('dashboard.viewAll') }}
              </n-button>
            </div>
            <div v-if="recentProfiles.length" class="activity-list">
              <div
                v-for="profile in recentProfiles"
                :key="profile.id"
                class="activity-item"
                @click="navigateTo(`/profile/${profile.id}`)"
              >
                <div class="activity-item__dot" />
                <div class="activity-item__content">
                  <span class="activity-item__title">{{ profile.title }}</span>
                  <span class="activity-item__time">{{ formatRelativeTime(profile.updated_at) }}</span>
                </div>
              </div>
            </div>
            <p v-else class="activity-empty">{{ t('dashboard.noRecentProfiles') }}</p>
          </div>

          <!-- Professors -->
          <div class="activity-column">
            <div class="activity-column__header">
              <span class="activity-column__title">{{ t('dashboard.recentProfessors') }}</span>
              <n-button v-if="recentProfessors.length" text type="primary" size="tiny" @click="navigateTo('/professor')">
                {{ t('dashboard.viewAll') }}
              </n-button>
            </div>
            <div v-if="recentProfessors.length" class="activity-list">
              <div
                v-for="prof in recentProfessors"
                :key="prof.id"
                class="activity-item"
                @click="navigateTo(`/professor/${prof.id}`)"
              >
                <div class="activity-item__dot" />
                <div class="activity-item__content">
                  <span class="activity-item__title">{{ prof.name }}</span>
                  <span class="activity-item__meta">{{ prof.affiliation }}</span>
                </div>
              </div>
            </div>
            <p v-else class="activity-empty">{{ t('dashboard.noRecentProfessors') }}</p>
          </div>

          <!-- Letters -->
          <div class="activity-column">
            <div class="activity-column__header">
              <span class="activity-column__title">{{ t('dashboard.recentLetters') }}</span>
              <n-button v-if="recentLetters.length" text type="primary" size="tiny" @click="navigateTo('/letter')">
                {{ t('dashboard.viewAll') }}
              </n-button>
            </div>
            <div v-if="recentLetters.length" class="activity-list">
              <div
                v-for="letter in recentLetters"
                :key="letter.professor_id"
                class="activity-item"
                @click="navigateTo(`/match?professor=${letter.professor_id}`)"
              >
                <div class="activity-item__dot" />
                <div class="activity-item__content">
                  <span class="activity-item__title">{{ letter.professor_name }}</span>
                  <span class="activity-item__meta">
                    {{ letter.generated_at ? formatRelativeTime(letter.generated_at) : t('dashboard.letterPending') }}
                  </span>
                </div>
              </div>
            </div>
            <p v-else class="activity-empty">{{ t('dashboard.noRecentLetters') }}</p>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1200px;
  animation: dashFadeIn 0.5s ease-out;
}

@keyframes dashFadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Hero */
.hero {
  margin-bottom: 36px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.hero-greeting {
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin: 0 0 6px;
  line-height: 1.2;
  color: var(--foreground);
}

.hero-quote {
  font-size: 1.1rem;
  color: var(--muted-foreground);
  margin: 24px 0 0;
  opacity: 0.8;
  line-height: 1.5;
}

/* Loading */
.loading-state {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

/* Section headings */
.section-heading {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted-foreground);
  margin: 0;
}

/* ---- Progress Flow ---- */
.flow-section {
  margin-bottom: 36px;
}

.flow-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.flow-steps {
  display: flex;
  gap: 0;
  margin-top: 16px;
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--card);
}

.flow-step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  cursor: pointer;
  transition: background 0.15s ease;
  position: relative;
  border-right: 1px solid var(--border);
}

.flow-step:last-child {
  border-right: none;
}

.flow-step:hover {
  background: var(--accent);
}

.flow-step--active {
  background: oklch(from var(--primary) l c h / 0.06);
}

.flow-step--done {
  opacity: 0.7;
}

.flow-step--done:hover {
  opacity: 1;
}

.flow-step__indicator {
  display: flex;
  align-items: center;
  position: relative;
  flex-shrink: 0;
}

.flow-step__check {
  color: var(--primary);
  display: flex;
}

.flow-step__circle {
  color: var(--muted-foreground);
  display: flex;
}

.flow-step__pulse {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--primary);
  position: relative;
}

.flow-step__pulse::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid var(--primary);
  opacity: 0.3;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.2); opacity: 0; }
}

.flow-step__connector {
  display: none;
}

.flow-step__content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.flow-step__label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--foreground);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.flow-step__desc {
  font-size: 0.72rem;
  color: var(--muted-foreground);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.flow-step__arrow {
  color: var(--muted-foreground);
  margin-left: auto;
  flex-shrink: 0;
  opacity: 0.4;
}

.flow-step:hover .flow-step__arrow {
  opacity: 1;
}

/* ---- Main Grid ---- */
.main-grid {
  display: grid;
  grid-template-columns: 1fr 1.3fr;
  gap: 20px;
  margin-bottom: 36px;
}

/* Profile Card */
.profile-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  background: var(--card);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.profile-card:hover {
  border-color: oklch(from var(--primary) l c h / 0.3);
  box-shadow: 0 2px 12px oklch(from var(--primary) l c h / 0.06);
}

.profile-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.profile-card__title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.profile-card__name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--foreground);
}

.profile-card__updated {
  font-size: 0.78rem;
  color: var(--muted-foreground);
  margin: 0 0 18px;
}

.profile-card__section {
  margin-bottom: 16px;
}

.profile-card__section:last-child {
  margin-bottom: 0;
}

.profile-card__section-label {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted-foreground);
  margin-bottom: 8px;
}

.profile-card__edu-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.profile-card__edu {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 0.82rem;
}

.profile-card__edu-degree {
  font-weight: 500;
  color: var(--foreground);
}

.profile-card__edu-school {
  color: var(--muted-foreground);
}

.profile-card__skills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.skill-chip {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 100px;
  background: var(--accent);
  color: var(--accent-foreground);
  border: 1px solid var(--border);
}

.skill-chip--more {
  background: transparent;
  color: var(--muted-foreground);
  border-style: dashed;
}

.profile-card__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 0;
  text-align: center;
  color: var(--muted-foreground);
  gap: 8px;
}

.profile-card__empty-icon {
  opacity: 0.3;
}

.profile-card__empty p {
  margin: 0;
  font-size: 0.85rem;
}

/* Matches Card */
.matches-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  background: var(--card);
}

.matches-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.matches-card__desc {
  font-size: 0.8rem;
  color: var(--muted-foreground);
  margin: 0 0 18px;
}

.match-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s ease;
}

.match-item:hover {
  background: var(--accent);
}

.match-item__rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--muted-foreground);
  background: var(--muted);
  border-radius: 6px;
  flex-shrink: 0;
}

.match-item:nth-child(1) .match-item__rank {
  background: oklch(from var(--primary) l c h / 0.15);
  color: var(--primary);
}

.match-item__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.match-item__name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--foreground);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.match-item__affiliation {
  font-size: 0.72rem;
  color: var(--muted-foreground);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.match-item__score-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.match-item__bar-bg {
  width: 72px;
  height: 6px;
  background: var(--muted);
  border-radius: 3px;
  overflow: hidden;
}

.match-item__bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

.match-item__score {
  font-size: 0.82rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  min-width: 36px;
  text-align: right;
}

.matches-card__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 0;
  text-align: center;
  color: var(--muted-foreground);
  gap: 12px;
}

.matches-card__empty-icon {
  opacity: 0.3;
}

.matches-card__empty p {
  margin: 0;
  font-size: 0.85rem;
}

/* ---- Activity Section ---- */
.activity-section {
  margin-bottom: 40px;
}

.activity-section .section-heading {
  margin-bottom: 16px;
}

.activity-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.activity-column {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  background: var(--card);
}

.activity-column__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.activity-column__title {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--foreground);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s ease;
}

.activity-item:hover {
  background: var(--accent);
}

.activity-item__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted-foreground);
  margin-top: 6px;
  flex-shrink: 0;
  opacity: 0.4;
}

.activity-item__content {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.activity-item__title {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--foreground);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-item__time,
.activity-item__meta {
  font-size: 0.72rem;
  color: var(--muted-foreground);
}

.activity-empty {
  text-align: center;
  padding: 24px 0;
  color: var(--muted-foreground);
  font-size: 0.82rem;
  margin: 0;
}

/* ---- Responsive ---- */
@media (max-width: 900px) {
  .flow-steps {
    flex-direction: column;
  }

  .flow-step {
    border-right: none;
    border-bottom: 1px solid var(--border);
  }

  .flow-step:last-child {
    border-bottom: none;
  }

  .main-grid {
    grid-template-columns: 1fr;
  }

  .activity-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .hero-greeting {
    font-size: 1.5rem;
  }

  .profile-card,
  .matches-card,
  .activity-column {
    padding: 16px;
  }
}

/* Dark mode adjustments */
:root.dark .flow-step--active {
  background: oklch(from var(--primary) l c h / 0.1);
}

:root.dark .match-item:nth-child(1) .match-item__rank {
  background: oklch(from var(--primary) l c h / 0.2);
}
</style>
