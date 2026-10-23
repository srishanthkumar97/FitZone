const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api').replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(message, status, payload = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export async function apiRequest(path, { method = 'GET', token, body, query } = {}) {
  const url = new URL(`${API_BASE_URL}/${path.replace(/^\/+/, '')}`)
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, value)
      }
    })
  }

  let response
  try {
    response = await fetch(url, {
      method,
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('Unable to reach FitZone right now. Check your connection and try again.', 0)
  }

  let payload = {}
  try {
    payload = await response.json()
  } catch {
    if (!response.ok) {
      throw new ApiError('The server returned an unreadable response.', response.status)
    }
    throw new ApiError('The server returned an unreadable response.', response.status)
  }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new ApiError('The server returned an unexpected response.', response.status)
  }

  if (!response.ok) {
    throw new ApiError(
      payload.message || 'Something went wrong. Please try again.',
      response.status,
      payload,
    )
  }
  return payload
}

export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  return error instanceof ApiError ? error.message : fallback
}
