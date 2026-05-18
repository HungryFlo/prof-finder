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
          redirect: '/profile',
        },
        {
          path: 'profile',
          name: 'ProfileList',
          component: () => import('@/views/profile/ProfileListView.vue'),
          meta: { breadcrumb: { labelKey: 'breadcrumb.profiles' } },
        },
        {
          path: 'profile/:id',
          name: 'ProfileDetail',
          component: () => import('@/views/profile/ProfileDetailView.vue'),
          meta: { breadcrumb: { labelKey: 'breadcrumb.profileDetail', dynamic: true } },
        },
        {
          path: 'professor',
          name: 'ProfessorList',
          component: () => import('@/views/professor/ProfessorListView.vue'),
          meta: { breadcrumb: { labelKey: 'breadcrumb.professors' } },
        },
        {
          path: 'professor/:id',
          name: 'ProfessorDetail',
          component: () => import('@/views/professor/ProfessorDetailView.vue'),
          meta: { breadcrumb: { labelKey: 'breadcrumb.professorDetail', dynamic: true } },
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
          name: 'LetterList',
          component: () => import('@/views/letter/LetterListView.vue'),
          meta: { breadcrumb: { labelKey: 'breadcrumb.letters' } },
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
