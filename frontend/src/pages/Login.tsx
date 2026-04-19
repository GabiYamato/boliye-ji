import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, setToken } from '../api'

const cid = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

export function Login() {
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [err, setErr] = useState('')

  async function submit(e: FormEvent) {
    e.preventDefault()
    setErr('')
    try {
      const path = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
      const data = await apiFetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      setToken(data.access_token)
      nav('/')
    } catch (x) {
      setErr(x instanceof Error ? x.message : 'failed')
    }
  }

  const form = (
    <form onSubmit={submit} className="mx-auto flex max-w-sm flex-col gap-3 text-left">
      <input
        className="rounded border border-neutral-600 bg-neutral-900 px-3 py-2 text-sm"
        placeholder="email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        className="rounded border border-neutral-600 bg-neutral-900 px-3 py-2 text-sm"
        placeholder="password (8+ chars)"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={8}
      />
      <button type="submit" className="rounded bg-emerald-600 py-2 text-sm font-medium text-white">
        {mode === 'login' ? 'Sign in' : 'Register'}
      </button>
      <button
        type="button"
        className="text-xs text-neutral-400 underline"
        onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
      >
        {mode === 'login' ? 'Need an account?' : 'Have an account?'}
      </button>
      {err && <p className="text-xs text-red-400">{err}</p>}
    </form>
  )

  const inner = (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 px-4">
      <h1 className="text-2xl font-semibold">Boliye</h1>
      {form}
      {cid ? (
        <GoogleLogin
          onSuccess={async (c) => {
            setErr('')
            try {
              const data = await apiFetch('/api/auth/google', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ credential: c.credential }),
              })
              setToken(data.access_token)
              nav('/')
            } catch (x) {
              setErr(x instanceof Error ? x.message : 'google failed')
            }
          }}
          onError={() => setErr('Google sign-in failed')}
        />
      ) : null}
    </div>
  )

  return cid ? <GoogleOAuthProvider clientId={cid}>{inner}</GoogleOAuthProvider> : inner
}
