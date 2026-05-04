import { Lock, UserPlus, Eye, EyeOff, Loader2 } from 'lucide-react'
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
  const [name, setName] = useState('')
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPass, setShowPass] = useState(false)

  const emailValid = /^\S+@\S+\.\S+$/.test(email)
  const passValid = password.length >= 8

  const canSubmit =
    emailValid && passValid && !loading && (mode === 'login' || name.trim().length > 0)

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    setErr('')
    setLoading(true)
    try {
      if (mode === 'register') {
        // Register first, then auto-login
        await apiFetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, name: name.trim() }),
        })
        // Auto-login after registration
        const data = await apiFetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        })
        setToken(data.access_token)
      } else {
        const data = await apiFetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        })
        setToken(data.access_token)
      }
      nav('/')
    } catch (x) {
      const msg = x instanceof Error ? x.message : 'Something went wrong'
      // Make common errors more user-friendly
      if (msg.includes('already registered')) {
        setErr('This email is already registered. Try signing in instead.')
      } else if (msg.includes('Invalid credentials')) {
        setErr('Wrong email or password. Please try again.')
      } else {
        setErr(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  function switchMode() {
    setMode(mode === 'login' ? 'register' : 'login')
    setErr('')
  }

  return (
    <MaybeGoogleProvider>
      <div className="flex min-h-[100dvh] items-center justify-center bg-[#111113] p-6 font-sans">
        <div className="w-full max-w-[420px] rounded-3xl border border-zinc-800/60 bg-[#161618] p-8 shadow-2xl shadow-black/50">
          {/* Header */}
          <div className="mb-8 flex flex-col items-center text-center">
            <div
              className="mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-zinc-800/80 text-zinc-100 shadow-inner transition-transform duration-300"
              style={{ transform: mode === 'register' ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
            >
              {mode === 'login' ? <Lock size={40} /> : <UserPlus size={40} />}
            </div>
            <h1 className="text-[26px] font-semibold tracking-tight text-white">
              {mode === 'login' ? 'Welcome back' : 'Create your account'}
            </h1>
            <p className="mt-2 text-sm text-zinc-400">
              {mode === 'login'
                ? 'Sign in to continue to Boliye.'
                : 'Get started with the voice assistant.'}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={submit} className="mx-auto flex w-full max-w-sm flex-col gap-4 text-left">
            {/* Name (register only) */}
            {mode === 'register' && (
              <div className="space-y-1.5">
                <label htmlFor="auth-name" className="text-sm font-medium text-zinc-400">
                  Your name
                </label>
                <input
                  id="auth-name"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900/50 px-4 py-2.5 text-sm text-zinc-100 outline-none transition focus:border-zinc-600 focus:bg-zinc-800"
                  placeholder="John Doe"
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
            )}

            {/* Email */}
            <div className="space-y-1.5">
              <label htmlFor="auth-email" className="text-sm font-medium text-zinc-400">
                Email address
              </label>
              <input
                id="auth-email"
                className={`w-full rounded-xl border bg-zinc-900/50 px-4 py-2.5 text-sm text-zinc-100 outline-none transition focus:bg-zinc-800 ${
                  email.length > 0 && !emailValid
                    ? 'border-red-500/50 focus:border-red-500/70'
                    : 'border-zinc-800 focus:border-zinc-600'
                }`}
                placeholder="you@example.com"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label htmlFor="auth-password" className="text-sm font-medium text-zinc-400">
                Password
              </label>
              <div className="relative">
                <input
                  id="auth-password"
                  className={`w-full rounded-xl border bg-zinc-900/50 px-4 py-2.5 pr-11 text-sm text-zinc-100 outline-none transition focus:bg-zinc-800 ${
                    password.length > 0 && !passValid
                      ? 'border-red-500/50 focus:border-red-500/70'
                      : 'border-zinc-800 focus:border-zinc-600'
                  }`}
                  placeholder={mode === 'register' ? 'Minimum 8 characters' : 'Your password'}
                  type={showPass ? 'text' : 'password'}
                  autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  tabIndex={-1}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 transition hover:text-zinc-300"
                  onClick={() => setShowPass(!showPass)}
                  aria-label={showPass ? 'Hide password' : 'Show password'}
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {password.length > 0 && !passValid && (
                <p className="text-xs text-red-400/80">Must be at least 8 characters</p>
              )}
            </div>

            {/* Error */}
            {err && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-center text-sm text-red-400">
                {err}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={!canSubmit}
              className="mt-1 flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-zinc-100 text-sm font-semibold tracking-wide text-zinc-900 transition hover:bg-white disabled:pointer-events-none disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Please wait...
                </>
              ) : mode === 'login' ? (
                'Sign in'
              ) : (
                'Create account'
              )}
            </button>

            {/* Toggle mode */}
            <button
              type="button"
              className="mt-1 text-sm font-medium text-zinc-500 transition hover:text-zinc-300"
              onClick={switchMode}
            >
              {mode === 'login'
                ? "Don't have an account? Sign up"
                : 'Already have an account? Sign in'}
            </button>
          </form>

          {/* Google OAuth */}
          {cid ? (
            <div className="mt-8 flex flex-col items-center justify-center border-t border-zinc-800 pt-6">
              <p className="mb-4 text-xs text-zinc-500">or continue with</p>
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
                    setErr(x instanceof Error ? x.message : 'Google sign-in failed')
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
    </MaybeGoogleProvider>
  )
}

/** Wraps children in GoogleOAuthProvider only if a client ID is configured */
function MaybeGoogleProvider({ children }: { children: React.ReactNode }) {
  if (cid) {
    return <GoogleOAuthProvider clientId={cid}>{children}</GoogleOAuthProvider>
  }
  return <>{children}</>
}
