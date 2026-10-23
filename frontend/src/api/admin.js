import { apiRequest } from './client'

export const getAdminDashboard = (token, query) =>
  apiRequest('/admin/dashboard', { token, query })
export const getMembers = (token, query) => apiRequest('/admin/members', { token, query })
export const getMember = (token, id) => apiRequest(`/admin/members/${id}`, { token })
export const createMember = (token, body) =>
  apiRequest('/admin/members', { method: 'POST', token, body })
export const updateMember = (token, id, body) =>
  apiRequest(`/admin/members/${id}`, { method: 'PUT', token, body })
export const deactivateMember = (token, id) =>
  apiRequest(`/admin/members/${id}`, { method: 'DELETE', token })
export const getMembershipPlans = (token) => apiRequest('/admin/membership-plans', { token })
export const createMembershipPlan = (token, body) =>
  apiRequest('/admin/membership-plans', { method: 'POST', token, body })
export const updateMembershipPlan = (token, id, body) =>
  apiRequest(`/admin/membership-plans/${id}`, { method: 'PUT', token, body })
export const deactivateMembershipPlan = (token, id) =>
  apiRequest(`/admin/membership-plans/${id}`, { method: 'DELETE', token })
export const assignMembership = (token, body) =>
  apiRequest('/admin/memberships', { method: 'POST', token, body })
export const renewMembership = (token, id, body) =>
  apiRequest(`/admin/memberships/${id}/renew`, { method: 'POST', token, body })
export const getAdminAttendance = (token, query) =>
  apiRequest('/admin/attendance', { token, query })
export const getTodayAttendance = (token) => apiRequest('/admin/attendance/today', { token })
export const getMemberAttendance = (token, id) =>
  apiRequest(`/admin/attendance/member/${id}`, { token })
export const getAttendanceStatistics = (token) =>
  apiRequest('/admin/attendance/statistics', { token })
export const getAnnouncements = (token) => apiRequest('/admin/announcements', { token })
export const createAnnouncement = (token, body) =>
  apiRequest('/admin/announcements', { method: 'POST', token, body })
export const updateAnnouncement = (token, id, body) =>
  apiRequest(`/admin/announcements/${id}`, { method: 'PUT', token, body })
export const deleteAnnouncement = (token, id) =>
  apiRequest(`/admin/announcements/${id}`, { method: 'DELETE', token })
