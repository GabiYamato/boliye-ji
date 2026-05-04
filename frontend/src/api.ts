const API = import.meta.env.VITE_API_URL || ''

export function getToken(): string | null {
  return localStorage.getItem('token')
}

export function setToken(t: string) {
  localStorage.setItem('token', t)
}

export function clearToken() {
  localStorage.removeItem('token')
}

/**
 * Wrapper around fetch that automatically attaches the auth token,
 * resolves the API base URL, and extracts user-friendly error messages
 * from FastAPI's JSON error responses.
 */
export async function apiFetch(path: string, init: RequestInit = {}) {
  const h = new Headers(init.headers)
  const t = getToken()
  if (t) h.set('Authorization', `Bearer ${t}`)
  const url = path.startsWith('http') ? path : `${API}${path}`
  const res = await fetch(url, { ...init, headers: h })

  if (!res.ok) {
    // FastAPI returns {"detail": "..."} for errors — extract the message
    let msg = res.statusText || 'Request failed'
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') {
        msg = body.detail
      } else if (typeof body?.message === 'string') {
        msg = body.message
      }
    } catch {
      // If body isn't JSON, try plain text
      try {
        const text = await res.text()
        if (text) msg = text
      } catch { /* ignore */ }
    }
    throw new Error(msg)
  }

  const ct = res.headers.get('content-type')
  if (ct?.includes('application/json')) return res.json()
  return res.text()
}
