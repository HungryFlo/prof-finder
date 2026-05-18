import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/change-password',
      name: 'ForceChangePassword',
      component: () => import('@/views/auth/ChangePasswordView.vue'),
      meta: { requiresAuth: true, allowMustChangePassword: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'profile',
          name: 'ProfileList',
          component: () => import('@/views/profile/ProfileListView.vue'),
        },
        {
          path: 'profile/:id',
          name: 'ProfileDetail',
          component: () => import('@/views/profile/ProfileDetailView.vue'),
        },
        {
          path: 'professor',
          name: 'ProfessorList',
          component: () => import('@/views/professor/ProfessorListView.vue'),
        },
        {
          path: 'professor/:id',
          name: 'ProfessorDetail',
          component: () => import('@/views/professor/ProfessorDetailView.vue'),
        },
        {
          path: 'professor/:id/edit',
          redirect: (to) => ({ path: `/professor/${to.params.id}` }),
        },
        {
          path: 'match',
          name: 'MatchResults',
          component: () => import('@/views/match/MatchResultsView.vue'),
        },
        {
          path: 'letter',
          name: 'LetterList',
          component: () => import('@/views/letter/LetterListView.vue'),
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/settings/SettingsView.vue'),
        },
        {
          path: 'admin/users',
          name: 'AdminUsers',
          component: () => import('@/views/admin/UsersView.vue'),
          meta: { requiresAdmin: true },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// Navigation guard
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Initialize auth state if needed
  if (authStore.accessToken && !authStore.user) {
    await authStore.init()
  }

  const requiresAuth = to.meta.requiresAuth !== false
  const requiresAdmin = to.meta.requiresAdmin === true
  const allowMustChangePassword = to.meta.allowMustChangePassword === true

  // Check authentication
  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // Check if user must change password
  if (
    requiresAuth &&
    authStore.mustChangePassword &&
    !allowMustChangePassword &&
    to.name !== 'ForceChangePassword'
  ) {
    next({ name: 'ForceChangePassword' })
    return
  }

  // Check admin permission
  if (requiresAdmin && !authStore.isAdmin) {
    next({ path: '/' })
    return
  }

  // Redirect authenticated users away from login/register
  if (!requiresAuth && authStore.isAuthenticated) {
    next({ path: '/' })
    return
  }

  next()
})

export default router
