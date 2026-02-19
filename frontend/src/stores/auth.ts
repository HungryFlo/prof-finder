import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const mustChangePassword = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  // Actions
  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearTokens() {
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function login(username: string, password: string) {
    const response = await authApi.login({ username, password })
    setTokens(response.access_token, response.refresh_token)
    mustChangePassword.value = response.must_change_password
    
    // Fetch user info
    await fetchUser()
    
    return response
  }

  async function register(username: string, password: string) {
    return await authApi.register({ username, password })
  }

  async function fetchUser() {
    if (!accessToken.value) return
    
    try {
      user.value = await authApi.getMe()
      mustChangePassword.value = user.value.must_change_password
    } catch {
      logout()
    }
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    const response = await authApi.changePassword({
      current_password: currentPassword,
      new_password: newPassword,
    })
    mustChangePassword.value = false
    return response
  }

  function logout() {
    user.value = null
    mustChangePassword.value = false
    clearTokens()
  }

  // Initialize: try to fetch user if token exists
  async function init() {
    if (accessToken.value) {
      await fetchUser()
    }
  }

  return {
    // State
    user,
    accessToken,
    refreshToken,
    mustChangePassword,
    // Getters
    isAuthenticated,
    isAdmin,
    // Actions
    setTokens,
    login,
    register,
    fetchUser,
    changePassword,
    logout,
    init,
  }
})
