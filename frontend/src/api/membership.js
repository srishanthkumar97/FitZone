import { apiRequest } from './client'

export const getPlans = () => apiRequest('/membership/plans')
export const getCurrentMembership = (token) => apiRequest('/membership/current', { token })
export const getMembershipHistory = (token) => apiRequest('/membership/history', { token })
