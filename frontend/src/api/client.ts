import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

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

      // Try to refresh token
      if (authStore.refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh', {
            refresh_token: authStore.refreshToken,
          })
          
          const { access_token, refresh_token } = response.data
          authStore.setTokens(access_token, refresh_token)
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return client(originalRequest)
        } catch {
          // Refresh failed, logout
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
