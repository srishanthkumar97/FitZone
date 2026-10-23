import { Navigate } from 'react-router-dom'
import { useAuth } from './authContext'

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { token, user } = useAuth()
  if (!token || !user || !['member', 'admin'].includes(user.role)) {
    return <Navigate to="/login" replace />
  }
  if (adminOnly && user.role !== 'admin') return <Navigate to="/dashboard" replace />
  if (!adminOnly && user.role !== 'member') return <Navigate to="/admin" replace />
  return children
}
