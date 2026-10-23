import { apiRequest } from './client'

export const getWorkouts = (token) => apiRequest('/workouts', { token })
export const createWorkout = (token, workout) =>
  apiRequest('/workouts', { method: 'POST', token, body: workout })
export const getProgress = (token) => apiRequest('/progress', { token })
export const createProgress = (token, progress) =>
  apiRequest('/progress', { method: 'POST', token, body: progress })
