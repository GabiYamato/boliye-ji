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

export async function apiFetch(path: string, init: RequestInit = {}) {
  const h = new Headers(init.headers)
  const t = getToken()
  if (t) h.set('Authorization', `Bearer ${t}`)
  const url = path.startsWith('http') ? path : `${API}${path}`
  const res = await fetch(url, { ...init, headers: h })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || res.statusText)
  }
  const ct = res.headers.get('content-type')
  if (ct?.includes('application/json')) return res.json()
  return res.text()
}
