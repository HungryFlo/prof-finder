import client from './client'
import type { User, TokenResponse } from '@/types'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export const authApi = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await client.post<TokenResponse>('/auth/login', data)
    return response.data
  },

  async register(data: RegisterRequest): Promise<User> {
    const response = await client.post<User>('/auth/register', data)
    return response.data
  },

  async refresh(refreshToken: string): Promise<TokenResponse> {
    const response = await client.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  async getMe(): Promise<User> {
    const response = await client.get<User>('/auth/me')
    return response.data
  },

  async changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
    const response = await client.post<{ message: string }>('/auth/change-password', data)
    return response.data
  },
}

// Admin API
export const adminApi = {
  async listUsers(): Promise<User[]> {
    const response = await client.get<User[]>('/admin/users')
    return response.data
  },

  async resetPassword(userId: number, newPassword: string): Promise<{ message: string }> {
    const response = await client.post<{ message: string }>(
      `/admin/users/${userId}/reset-password`,
      { new_password: newPassword }
    )
    return response.data
  },
}
