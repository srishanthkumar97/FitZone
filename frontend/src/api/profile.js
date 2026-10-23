import { apiRequest } from './client'

export const getProfile = (token) => apiRequest('/auth/me', { token })
export const updateProfile = (token, values) =>
  apiRequest('/auth/profile', { method: 'PUT', token, body: values })
