import { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, clearToken, getToken } from '../api'
import { VoiceOrb, type VoicePhase } from '../components/VoiceOrb'

type Msg = { role: 'user' | 'assistant'; content: string }

export function Chat() {
  const nav = useNavigate()
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [voicePhase, setVoicePhase] = useState<VoicePhase>('idle')
  const recRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<BlobPart[]>([])

  const logout = () => {
    clearToken()
    nav('/login')
  }

  const sendText = async () => {
    const text = input.trim()
    if (!text || loading) return
    const next: Msg[] = [...messages, { role: 'user', content: text }]
    setMessages(next)
    setInput('')
    setLoading(true)
    try {
      const data = await apiFetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: next.map((m) => ({ role: m.role, content: m.content })),
        }),
      })
      setMessages([...next, { role: 'assistant', content: data.reply }])
    } finally {
      setLoading(false)
    }
  }

  const stopRecording = useCallback(async () => {
    const rec = recRef.current
    if (!rec || rec.state === 'inactive') return
    rec.stop()
    recRef.current = null
    setVoicePhase('thinking')
  }, [])

  const startVoice = async () => {
    if (!getToken() || loading) return
    setVoicePhase('listening')
    chunksRef.current = []
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setVoicePhase('idle')
      return
    }
    const rec = new MediaRecorder(stream, { mimeType: 'audio/webm' })
    recRef.current = rec
    rec.ondataavailable = (e) => {
      if (e.data.size) chunksRef.current.push(e.data)
    }
    rec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop())
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
      chunksRef.current = []
      const fd = new FormData()
      fd.append('audio', blob, 'speech.webm')
      fd.append(
        'messages',
        JSON.stringify(messages.map((m) => ({ role: m.role, content: m.content }))),
      )
      try {
        const data = await apiFetch('/api/voice/process', { method: 'POST', body: fd })
        const userMsg: Msg = { role: 'user', content: data.transcript }
        const asstMsg: Msg = { role: 'assistant', content: data.reply }
        setMessages((prev) => [...prev, userMsg, asstMsg])
        setVoicePhase('speaking')
        const bin = atob(data.audio_base64 as string)
        const bytes = new Uint8Array(bin.length)
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
        const url = URL.createObjectURL(new Blob([bytes], { type: data.audio_mime || 'audio/mpeg' }))
        const a = new Audio(url)
        a.onended = () => {
          URL.revokeObjectURL(url)
          setVoicePhase('idle')
        }
        await a.play()
      } catch {
        setVoicePhase('idle')
      } finally {
        setLoading(false)
      }
    }
    setLoading(true)
    rec.start()
    window.setTimeout(() => {
      void stopRecording()
    }, 6000)
  }

  return (
    <div className="flex h-[100dvh] flex-col bg-[#212121]">
      <header className="flex items-center justify-between border-b border-neutral-700 px-4 py-3">
        <span className="font-medium">Boliye</span>
        <button type="button" className="text-sm text-neutral-400 hover:text-white" onClick={logout}>
          Log out
        </button>
      </header>
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm leading-relaxed ${
                m.role === 'user' ? 'ml-auto bg-neutral-700' : 'mr-auto bg-neutral-800'
              }`}
            >
              {m.content}
            </div>
          ))}
        </div>
        <div className="border-t border-neutral-700 p-4">
          <div className="mx-auto flex max-w-3xl flex-col gap-3">
            <div className="flex justify-center">
              <VoiceOrb phase={loading && voicePhase === 'idle' ? 'thinking' : voicePhase} />
            </div>
            <div className="flex gap-2">
              <textarea
                className="min-h-[44px] flex-1 resize-none rounded-xl border border-neutral-600 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-emerald-600"
                placeholder="Message…"
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    void sendText()
                  }
                }}
              />
              <button
                type="button"
                disabled={loading}
                className="rounded-xl bg-emerald-600 px-4 text-sm font-medium text-white disabled:opacity-50"
                onClick={() => void sendText()}
              >
                Send
              </button>
              <button
                type="button"
                disabled={loading}
                className="rounded-xl border border-neutral-500 px-3 text-sm text-neutral-200 disabled:opacity-50"
                onClick={() => void startVoice()}
              >
                Voice
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
