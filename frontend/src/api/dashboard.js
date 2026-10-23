import { apiRequest } from './client'

export async function getMemberDashboard(token) {
  const response = await apiRequest('/dashboard', { token })

  if (!response || typeof response !== 'object' || Array.isArray(response)) {
    throw new Error('The dashboard response was empty or invalid. Please try again.')
  }

  if (response.success !== true) {
    throw new Error(response.message || 'Unable to load dashboard. Please try again.')
  }

  const isRecord = (value) => value !== null && typeof value === 'object' && !Array.isArray(value)
  const isRecordArray = (value) => Array.isArray(value) && value.every(isRecord)
  const hasDashboardData = (
    isRecord(response.user)
    && isRecord(response.attendance)
    && (response.membership === null || isRecord(response.membership))
    && (response.progress === null || isRecord(response.progress))
    && isRecordArray(response.recent_workouts)
    && isRecordArray(response.recent_notifications)
  )

  if (!hasDashboardData) {
    throw new Error('The dashboard response is incomplete. Please try again.')
  }

  return response
}
