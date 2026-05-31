import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSetupGate } from '@/composables/useSetupGate'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/setup',
      name: 'Setup',
      component: () => import('@/views/setup/SetupView.vue'),
      meta: { requiresAuth: false, setupOnly: true },
    },
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
          meta: { breadcrumb: { labelKey: 'breadcrumb.profiles' } },
          children: [
            {
              path: '',
              name: 'ProfileList',
              component: () => import('@/views/profile/ProfileListView.vue'),
            },
            {
              path: ':id',
              name: 'ProfileDetail',
              component: () => import('@/views/profile/ProfileDetailView.vue'),
              meta: { breadcrumb: { labelKey: 'breadcrumb.profileDetail', dynamic: true } },
            },
          ],
        },
        {
          path: 'professor',
          meta: { breadcrumb: { labelKey: 'breadcrumb.professors' } },
          children: [
            {
              path: '',
              name: 'ProfessorList',
              component: () => import('@/views/professor/ProfessorListView.vue'),
            },
            {
              path: ':id',
              name: 'ProfessorDetail',
              component: () => import('@/views/professor/ProfessorDetailView.vue'),
              meta: { breadcrumb: { labelKey: 'breadcrumb.professorDetail', dynamic: true } },
            },
          ],
        },
        {
          path: 'professor/:id/edit',
          redirect: (to) => ({ path: `/professor/${to.params.id}` }),
        },
        {
          path: 'match',
          name: 'MatchResults',
          component: () => import('@/views/match/MatchResultsView.vue'),
          meta: { breadcrumb: { labelKey: 'breadcrumb.match' } },
        },
        {
          path: 'letter',
          redirect: '/match',
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/settings/SettingsView.vue'),
          meta: { breadcrumb: { labelKey: 'breadcrumb.settings' } },
        },
        {
          path: 'admin/users',
          name: 'AdminUsers',
          component: () => import('@/views/admin/UsersView.vue'),
          meta: { requiresAdmin: true, breadcrumb: { labelKey: 'breadcrumb.adminUsers' } },
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
  const { requiresSetup, ensureStatus } = useSetupGate()

  if (to.name !== 'Setup') {
    try {
      if (await requiresSetup()) {
        next({ name: 'Setup' })
        return
      }
    } catch {
      // Allow navigation if setup status cannot be loaded (e.g. API down).
    }
  } else {
    try {
      const status = await ensureStatus()
      if (!status.packaged || status.configured) {
        next({ name: 'Login' })
        return
      }
    } catch {
      next({ name: 'Login' })
      return
    }
  }

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
