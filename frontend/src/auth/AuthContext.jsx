import { useState } from 'react'
import { AuthContext } from './authContext'
import * as authApi from '../api/auth'
import * as profileApi from '../api/profile'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)

  async function signIn(credentials) {
    const result = await authApi.login(credentials)
    if (
      !result
      || typeof result.token !== 'string'
      || !result.token
      || !result.user
      || typeof result.user !== 'object'
      || Array.isArray(result.user)
      || typeof result.user.name !== 'string'
      || typeof result.user.email !== 'string'
      || !['member', 'admin'].includes(result.user.role)
    ) {
      throw new Error('The sign-in response was incomplete. Please try again.')
    }
    setToken(result.token)
    setUser(result.user)
    return result.user
  }

  async function signUp(details) {
    return authApi.register(details)
  }

  async function refreshProfile() {
    if (!token) return null
    const result = await profileApi.getProfile(token)
    if (
      !result?.user
      || typeof result.user !== 'object'
      || Array.isArray(result.user)
      || typeof result.user.name !== 'string'
      || typeof result.user.email !== 'string'
      || !['member', 'admin'].includes(result.user.role)
    ) {
      throw new Error('The profile response was incomplete. Please try again.')
    }
    setUser(result.user)
    return result.user
  }

  function signOut() {
    setToken(null)
    setUser(null)
  }

  const value = { token, user, signIn, signUp, signOut, refreshProfile }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
