import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// Shared promise to deduplicate concurrent token refresh requests
let refreshPromise: Promise<string> | null = null

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore()
    // Ensure FormData requests are sent as multipart/form-data with boundary.
    // If JSON content-type is kept, backend File/Form fields will be missing.
    if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
      if (config.headers && typeof (config.headers as any).delete === 'function') {
        ;(config.headers as any).delete('Content-Type')
      } else if (config.headers) {
        delete (config.headers as any)['Content-Type']
      }
    }

    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors and token refresh
client.interceptors.response.use(
  (response) => {
    return response
  },
  async (error: AxiosError) => {
    const authStore = useAuthStore()
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Handle 401 errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // Try to refresh token — deduplicate concurrent refresh requests
      if (authStore.refreshToken) {
        try {
          if (!refreshPromise) {
            refreshPromise = axios
              .post('/api/auth/refresh', {
                refresh_token: authStore.refreshToken,
              })
              .then((res) => {
                const { access_token, refresh_token } = res.data
                authStore.setTokens(access_token, refresh_token)
                return access_token as string
              })
              .finally(() => {
                refreshPromise = null
              })
          }
          const newToken = await refreshPromise

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return client(originalRequest)
        } catch {
          // Refresh failed, logout
          refreshPromise = null
          authStore.logout()
          router.push('/login')
        }
      } else {
        authStore.logout()
        router.push('/login')
      }
    }

    return Promise.reject(error)
  }
)

export default client
