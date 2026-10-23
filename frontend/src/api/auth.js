import { apiRequest } from './client'

export const login = (credentials) => apiRequest('/auth/login', { method: 'POST', body: credentials })
export const register = (details) => apiRequest('/auth/register', { method: 'POST', body: details })
export const getMe = (token) => apiRequest('/auth/me', { token })
