import { MessageCircle, Plus, MessageSquare, LogOut, Mic, ArrowRight } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, clearToken, getToken } from '../api'
import type { VoicePhase } from '../components/VoiceOrb'
import { VoiceScreen } from '../components/VoiceScreen'

type Msg = { role: 'user' | 'assistant'; content: string }

function pickRecorderMime(): string {
  const preferred = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/aac']
  for (const m of preferred) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(m)) return m
  }
  return 'audio/webm'
}

function extFromMime(mime: string): string {
  if (mime.includes('mp4')) return 'mp4'
  if (mime.includes('aac')) return 'aac'
  if (mime.includes('ogg')) return 'ogg'
  return 'webm'
}

function decodeAudio(base64: string, mime: string) {
  const bin = atob(base64)
  const bytes = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  return new Blob([bytes], { type: mime })
}

export function Chat() {
  const nav = useNavigate()
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [voicePhase, setVoicePhase] = useState<VoicePhase>('idle')
  const [voiceOpen, setVoiceOpen] = useState(false)
  const [liveTranscript, setLiveTranscript] = useState('')
  const [voiceLevel, setVoiceLevel] = useState(0.08)
  const [err, setErr] = useState('')

  const recRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const transcriptRef = useRef('')
  const analyserCtxRef = useRef<AudioContext | null>(null)
  const analyserNodeRef = useRef<AnalyserNode | null>(null)
  const levelTimerRef = useRef<number | null>(null)
  const stopTimerRef = useRef<number | null>(null)
  const transcribingRef = useRef(false)
  const phaseRef = useRef<VoicePhase>('idle')
  const recorderMimeRef = useRef('audio/webm')
  const sessionActiveRef = useRef(false)
  const messagesRef = useRef<Msg[]>([])
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    messagesRef.current = messages
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, liveTranscript, err])

  const fetchHistory = async () => {
    try {
      const data = await apiFetch('/api/chat/history', { method: 'GET' })
      if (Array.isArray(data)) {
        setMessages(data)
      }
    } catch (e) {
      console.error('Failed to load history', e)
    }
  }

  const clearHistory = async () => {
    try {
      await apiFetch('/api/chat/history', { method: 'DELETE' })
      setMessages([])
      setErr('')
      setLiveTranscript('')
    } catch (e) {
      console.error('Failed to clear history', e)
    }
  }

  useEffect(() => {
    if (getToken()) {
      void fetchHistory()
    }
  }, [])

  const logout = () => {
    clearToken()
    nav('/login')
  }

  const sendText = async () => {
    const text = input.trim()
    if (!text || loading) return
    setErr('')
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
    } catch (x) {
      setErr(x instanceof Error ? x.message : 'request failed')
    } finally {
      setLoading(false)
    }
  }

  const stopLevelMeter = () => {
    if (levelTimerRef.current) {
      window.clearInterval(levelTimerRef.current)
      levelTimerRef.current = null
    }
    analyserNodeRef.current = null
    if (analyserCtxRef.current) {
      void analyserCtxRef.current.close()
      analyserCtxRef.current = null
    }
  }

  const startLevelMeter = (stream: MediaStream) => {
    stopLevelMeter()
    const ac = new AudioContext()
    const src = ac.createMediaStreamSource(stream)
    const analyser = ac.createAnalyser()
    analyser.fftSize = 256
    src.connect(analyser)
    analyserCtxRef.current = ac
    analyserNodeRef.current = analyser
    const arr = new Uint8Array(analyser.frequencyBinCount)
    levelTimerRef.current = window.setInterval(() => {
      if (!analyserNodeRef.current) return
      analyserNodeRef.current.getByteTimeDomainData(arr)
      let s = 0
      for (let i = 0; i < arr.length; i++) {
        const n = (arr[i] - 128) / 128
        s += n * n
      }
      const rms = Math.sqrt(s / arr.length)
      const normalized = Math.min(1, rms * 5.2 + 0.03)
      setVoiceLevel(normalized)
    }, 80)
  }

  const stopVoiceSession = () => {
    if (stopTimerRef.current) {
      window.clearTimeout(stopTimerRef.current)
      stopTimerRef.current = null
    }
    const rec = recRef.current
    if (rec && rec.state !== 'inactive') rec.stop()
    recRef.current = null
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    stopLevelMeter()
    transcribingRef.current = false
  }

  const playWithMeter = async (audioBlob: Blob) => {
    const ac = new AudioContext()
    const arr = await audioBlob.arrayBuffer()
    const buff = await ac.decodeAudioData(arr.slice(0))
    const source = ac.createBufferSource()
    const analyser = ac.createAnalyser()
    analyser.fftSize = 256
    source.buffer = buff
    source.connect(analyser)
    analyser.connect(ac.destination)
    const probe = new Uint8Array(analyser.frequencyBinCount)
    const meter = window.setInterval(() => {
      analyser.getByteTimeDomainData(probe)
      let s = 0
      for (let i = 0; i < probe.length; i++) {
        const n = (probe[i] - 128) / 128
        s += n * n
      }
      const rms = Math.sqrt(s / probe.length)
      setVoiceLevel(Math.min(1, rms * 8 + 0.05))
    }, 80)

    await new Promise<void>((resolve) => {
      source.onended = () => {
        window.clearInterval(meter)
        void ac.close()
        resolve()
      }
      source.start(0)
    })
  }

  const transcribeChunk = async (blob: Blob, ext: string) => {
    if (transcribingRef.current || blob.size < 1024) return
    transcribingRef.current = true
    const fd = new FormData()
    fd.append('audio', blob, `chunk-${Date.now()}.${ext}`)
    try {
      const data = await apiFetch('/api/voice/transcribe', { method: 'POST', body: fd })
      const t = String(data.transcript || '').trim()
      if (t) {
        transcriptRef.current = t
        setLiveTranscript(t)
      }
    } catch {
      // ignore chunk errors while streaming
    } finally {
      transcribingRef.current = false
    }
  }

  const startVoice = async () => {
    if (!getToken() || loading) return
    setErr('')
    setLiveTranscript('')
    transcriptRef.current = ''
    setVoiceOpen(true)
    sessionActiveRef.current = true
    setVoicePhase('listening')
    chunksRef.current = []
    let stream: MediaStream
    try {
      if (streamRef.current) {
        stream = streamRef.current
      } else {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        streamRef.current = stream
      }
    } catch {
      setVoicePhase('idle')
      setVoiceOpen(false)
      sessionActiveRef.current = false
      setErr('Microphone access denied')
      return
    }
    startLevelMeter(stream)
    const recorderMime = pickRecorderMime()
    recorderMimeRef.current = recorderMime
    const rec = new MediaRecorder(stream, { mimeType: recorderMime })
    recRef.current = rec
    rec.ondataavailable = async (e) => {
      if (e.data.size) chunksRef.current.push(e.data)
      if (phaseRef.current === 'listening') {
        const ext = extFromMime(recorderMimeRef.current)
        const progressive = new Blob(chunksRef.current, { type: recorderMimeRef.current })
        await transcribeChunk(progressive, ext)
      }
    }
    rec.onstop = async () => {
      stopLevelMeter()
      const blob = new Blob(chunksRef.current, { type: recorderMimeRef.current })
      chunksRef.current = []
      const fd = new FormData()
      const ext = extFromMime(recorderMimeRef.current)
      fd.append('audio', blob, `speech.${ext}`)
      
      fd.append(
        'messages',
        JSON.stringify(messagesRef.current.map((m) => ({ role: m.role, content: m.content }))),
      )
      
      try {
        const data = await apiFetch('/api/voice/process', { method: 'POST', body: fd })
        const userMsg: Msg = { role: 'user', content: data.transcript }
        const asstMsg: Msg = { role: 'assistant', content: data.reply }
        setMessages((prev) => [...prev, userMsg, asstMsg])
        setLiveTranscript(data.reply)
        
        if (!sessionActiveRef.current) return

        // Play TTS audio if available, otherwise skip playback
        if (data.audio_base64) {
          setVoicePhase('speaking')
          const audioBlob = decodeAudio(String(data.audio_base64), String(data.audio_mime || 'audio/wav'))
          await playWithMeter(audioBlob)
        }
        
        if (sessionActiveRef.current) {
          // Update the ref immediately before recursively calling startVoice
          // so the next iteration has the updated state even if React hasn't re-rendered yet.
          messagesRef.current = [...messagesRef.current, userMsg, asstMsg]
          setLoading(false)
          startVoice()
        }
      } catch (x) {
        setVoicePhase('idle')
        setVoiceOpen(false)
        sessionActiveRef.current = false
        setErr(x instanceof Error ? x.message : 'voice request failed')
      } finally {
        setLoading(false)
      }
    }
    setLoading(true)
    rec.start(700)
    stopTimerRef.current = window.setTimeout(() => {
      if (!recRef.current || recRef.current.state === 'inactive') return
      setVoicePhase('thinking')
      recRef.current.stop()
      recRef.current = null
    }, 7600)
  }

  const stopListeningNow = () => {
    if (!recRef.current || recRef.current.state === 'inactive') return
    setVoicePhase('thinking')
    recRef.current.stop()
    recRef.current = null
  }

  const cancelVoice = () => {
    sessionActiveRef.current = false
    stopVoiceSession()
    setVoiceOpen(false)
    setVoicePhase('idle')
    setVoiceLevel(0.08)
    setLoading(false)
  }

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading])

  useEffect(() => {
    phaseRef.current = voicePhase
  }, [voicePhase])

  useEffect(() => {
    return () => {
      stopVoiceSession()
    }
  }, [])

  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-[#111113] text-zinc-100 font-sans">
      {/* Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-zinc-800/80 bg-[#161618] px-4 py-6 sm:flex">
        <div className="mb-8 flex items-center gap-3 px-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800 text-zinc-100 shadow-inner">
            <MessageCircle size={18} />
          </div>
          <span className="text-lg font-semibold tracking-wide text-white">boliye</span>
        </div>
        
        <button
          onClick={() => void clearHistory()}
          className="mb-6 flex w-full items-center justify-between rounded-full border border-zinc-700/50 bg-[#2A2A2C]/50 px-4 py-2.5 text-sm font-medium text-zinc-200 transition hover:bg-zinc-800"
        >
          <div className="flex items-center gap-2">
            <Plus size={16} />
            New Thread
          </div>
          <kbd className="hidden rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400 md:inline-block">⌘ K</kbd>
        </button>

        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto">
          <div className="mb-2 px-2 text-xs font-semibold tracking-wider text-zinc-500">History</div>
          {messages.length > 0 && (
            <button className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-sm text-zinc-300 hover:bg-zinc-800/60">
              <MessageSquare size={16} className="text-zinc-500" />
              <span className="truncate text-left text-zinc-300">Current conversation</span>
            </button>
          )}
        </nav>

        <div className="mt-auto border-t border-zinc-800/60 pt-4">
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-sm font-medium text-zinc-400 transition hover:bg-zinc-800 hover:text-zinc-200"
          >
            <LogOut size={20} />
            Log out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="relative flex flex-1 flex-col overflow-hidden">
        {/* Mobile Header */}
        <header className="flex shrink-0 items-center justify-between border-b border-zinc-800/60 bg-[#161618] px-4 py-3 sm:hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-zinc-800 text-zinc-100 shadow-inner">
              <MessageCircle size={14} />
            </div>
            <span className="font-semibold text-white">boliye</span>
          </div>
          <button type="button" className="text-zinc-400 hover:text-zinc-200" onClick={logout}>
            <LogOut size={20} />
          </button>
        </header>

        <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-0">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center pb-20">
                <h1 className="text-4xl font-semibold tracking-tight text-white mb-10">boliye</h1>
              </div>
            ) : (
              <div className="space-y-6 pb-20">
                {messages.map((m, i) => (
                  <div key={i} className="flex flex-col">
                    {m.role === 'user' ? (
                      <div className="ml-auto max-w-[85%] rounded-3xl rounded-tr-sm bg-zinc-800 px-5 py-3 text-[15px] leading-relaxed text-zinc-100 shadow-sm">
                        {m.content}
                      </div>
                    ) : (
                      <div className="mr-auto flex max-w-[90%] gap-4">
                        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-zinc-100">
                          <MessageCircle size={16} />
                        </div>
                        <div className="prose prose-invert max-w-none text-[15px] leading-relaxed text-zinc-300">
                          {m.content}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {err && (
                  <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-center text-sm text-red-400">
                    {err}
                  </div>
                )}
                {loading && !voiceOpen && (
                  <div className="flex gap-2 p-4 text-zinc-500">
                    <span className="flex h-2 w-2 animate-pulse rounded-full bg-zinc-500"></span>
                    <span className="flex h-2 w-2 animate-pulse rounded-full bg-zinc-500" style={{ animationDelay: '0.2s' }}></span>
                    <span className="flex h-2 w-2 animate-pulse rounded-full bg-zinc-500" style={{ animationDelay: '0.4s' }}></span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#111113] via-[#111113] to-transparent pt-10 pb-6 px-4 sm:px-8">
            <div className="mx-auto max-w-3xl">
              <div className="relative flex flex-col rounded-2xl border border-zinc-700/50 bg-[#202022] p-2 shadow-xl focus-within:border-zinc-500 focus-within:ring-1 focus-within:ring-zinc-500">
                <textarea
                  className="max-h-48 min-h-[44px] w-full resize-none border-0 bg-transparent px-3 py-3 text-[15px] leading-relaxed text-zinc-100 placeholder-zinc-500 outline-none focus:ring-0"
                  placeholder="Ask anything..."
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
                <div className="flex items-center justify-between px-2 pb-1 pt-2">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={loading}
                      className="flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium text-zinc-400 transition hover:bg-zinc-800 hover:text-zinc-200 disabled:opacity-50"
                      onClick={() => void startVoice()}
                    >
                      <Mic size={16} />
                      Voice
                    </button>
                  </div>
                  <button
                    type="button"
                    disabled={!canSend}
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-100 text-zinc-900 transition hover:bg-white disabled:bg-zinc-800 disabled:text-zinc-600"
                    onClick={() => void sendText()}
                  >
                    <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        {voiceOpen ? (
          <VoiceScreen
            phase={voicePhase}
            transcript={liveTranscript}
            level={voiceLevel}
            onCancel={cancelVoice}
            onStop={stopListeningNow}
          />
        ) : null}
      </div>
    </div>
  )
}
