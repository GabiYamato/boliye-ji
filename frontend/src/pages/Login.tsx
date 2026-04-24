import { Lock, UserPlus } from 'lucide-react'
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
  const [loading, setLoading] = useState(false)

  const emailValid = /^\S+@\S+\.\S+$/.test(email)
  const passValid = password.length >= 8

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!emailValid || !passValid || loading) return
    setErr('')
    setLoading(true)
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
    } finally {
      setLoading(false)
    }
  }

  const form = (
    <form onSubmit={submit} className="mx-auto flex w-full max-w-sm flex-col gap-4 text-left">
      <div className="space-y-1.5">
        <label className="text-sm font-medium text-zinc-400">Email address</label>
        <input
          className={`w-full rounded-xl border bg-zinc-900/50 px-4 py-2.5 text-sm text-zinc-100 outline-none transition focus:bg-zinc-800 ${
            email.length > 0 && !emailValid
              ? 'border-red-500/50 focus:border-red-500/70'
              : 'border-zinc-800 focus:border-zinc-600'
          }`}
          placeholder="you@example.com"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <label className="text-sm font-medium text-zinc-400">Password</label>
        <input
          className={`w-full rounded-xl border bg-zinc-900/50 px-4 py-2.5 text-sm text-zinc-100 outline-none transition focus:bg-zinc-800 ${
            password.length > 0 && !passValid
              ? 'border-red-500/50 focus:border-red-500/70'
              : 'border-zinc-800 focus:border-zinc-600'
          }`}
          placeholder="Minimum 8 characters"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
        />
      </div>
      <button
        type="submit"
        disabled={loading || !emailValid || !passValid}
        className="mt-2 flex h-11 w-full items-center justify-center rounded-xl bg-zinc-100 pb-0.5 text-sm font-semibold tracking-wide text-zinc-900 transition hover:bg-white disabled:pointer-events-none disabled:opacity-50"
      >
        {loading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
      </button>
      <button
        type="button"
        className="mt-1 text-sm font-medium text-zinc-500 transition hover:text-zinc-300"
        onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
      >
        {mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
      </button>
      {err && <p className="text-center text-sm font-medium text-red-500">{err}</p>}
    </form>
  )

  const inner = (
    <div className="flex min-h-[100dvh] items-center justify-center bg-[#111113] p-6 font-sans">
      <div className="w-full max-w-[420px] rounded-3xl border border-zinc-800/60 bg-[#161618] p-8 shadow-2xl shadow-black/50">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-zinc-800/80 text-zinc-100 shadow-inner">
            {mode === 'login' ? <Lock size={40} /> : <UserPlus size={40} />}
          </div>
          <h1 className="text-[26px] font-semibold tracking-tight text-white">
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h1>
          <p className="mt-2 text-sm text-zinc-400">
            {mode === 'login'
              ? 'Enter your credentials to access Boliye.'
              : 'Sign up to start using the local voice assistant.'}
          </p>
        </div>
      {form}
        {cid ? (
          <div className="mt-8 flex flex-col items-center justify-center border-t border-zinc-800 pt-6">
            <GoogleLogin
              theme="filled_black"
              shape="pill"
              onSuccess={async (c) => {
                setErr('')
                setLoading(true)
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
                } finally {
                  setLoading(false)
                }
              }}
              onError={() => setErr('Google sign-in failed')}
            />
          </div>
        ) : null}
      </div>
    </div>
  )

  return cid ? <GoogleOAuthProvider clientId={cid}>{inner}</GoogleOAuthProvider> : inner
}
