import { apiRequest } from './client'

export const checkIn = (token) => apiRequest('/attendance/check-in', { method: 'POST', token, body: {} })
export const checkOut = (token) => apiRequest('/attendance/check-out', { method: 'POST', token, body: {} })
export const getAttendanceHistory = (token, query = {}) =>
  apiRequest('/attendance/history', { token, query })
export const getAttendanceSummary = (token) => apiRequest('/attendance/summary', { token })
