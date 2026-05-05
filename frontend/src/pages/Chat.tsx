import { MessageCircle, Plus, MessageSquare, LogOut, Mic, ArrowRight } from 'lucide-react'
import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
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
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [sessionId, setSessionId] = useState<string>('default')
  const [sessions, setSessions] = useState<{id: string, preview: string}[]>([])

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
  const fillerAudioCtxRef = useRef<AudioContext | null>(null)
  const fillerSourceRef = useRef<AudioBufferSourceNode | null>(null)
  const progressTimerRef = useRef<number | null>(null)
  const voiceAbortRef = useRef<AbortController | null>(null)
  const thinkingDoneRef = useRef(false)

  useEffect(() => {
    messagesRef.current = messages
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, liveTranscript, err])

  // ── History helpers ──────────────────────────────────────────
  const fetchSessions = useCallback(async () => {
    try {
      const data = await apiFetch('/api/chat/sessions', { method: 'GET' })
      if (Array.isArray(data)) {
        setSessions(data)
        if (data.length > 0 && sessionId === 'default') {
          setSessionId(data[0].id)
        }
      }
    } catch (e) {
      console.error('Failed to load sessions', e)
    }
  }, [sessionId])

  const fetchHistory = useCallback(async (sid: string) => {
    setHistoryLoaded(false)
    try {
      const data = await apiFetch(`/api/chat/history?session_id=${sid}`, { method: 'GET' })
      if (Array.isArray(data)) {
        setMessages(data)
        messagesRef.current = data
      }
    } catch (e) {
      console.error('Failed to load history', e)
    } finally {
      setHistoryLoaded(true)
    }
  }, [])

  const createNewThread = () => {
    setSessionId(crypto.randomUUID())
    setMessages([])
    messagesRef.current = []
    setErr('')
    setLiveTranscript('')
  }

  useEffect(() => {
    if (getToken()) {
      void fetchSessions()
    } else {
      setHistoryLoaded(true)
    }
  }, [fetchSessions])

  useEffect(() => {
    if (getToken()) {
      void fetchHistory(sessionId)
    }
  }, [sessionId, fetchHistory])

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
    messagesRef.current = next
    setInput('')
    setLoading(true)
    try {
      const token = getToken()
      const res = await fetch('/api/chat/message_stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          session_id: sessionId,
          messages: next.map((m) => ({ role: m.role, content: m.content })),
        }),
      })

      if (!res.ok) throw new Error('Chat request failed')
      if (!res.body) throw new Error('No response body')

      let assistantText = ''
      const base = [...next, { role: 'assistant' as const, content: '' }]
      setMessages(base)
      messagesRef.current = base

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'token') {
              assistantText += String(data.token || '')
              setMessages((prev) => {
                const updated = [...prev]
                if (updated.length) {
                  updated[updated.length - 1] = { role: 'assistant', content: assistantText }
                }
                return updated
              })
              messagesRef.current = [...messagesRef.current.slice(0, -1), { role: 'assistant', content: assistantText }]
            } else if (data.type === 'done') {
              break
            }
          } catch (e) {
            console.warn('Failed to parse chat stream line', e)
          }
        }
      }
      void fetchSessions()
    } catch (x) {
      setErr(x instanceof Error ? x.message : 'request failed')
    } finally {
      setLoading(false)
    }
  }

  // ── Filler audio helpers ────────────────────────────────────
  const stopFillerAudio = () => {
    if (fillerSourceRef.current) {
      try { fillerSourceRef.current.stop() } catch { /* ignore */ }
      fillerSourceRef.current = null
    }
    if (fillerAudioCtxRef.current) {
      try { void fillerAudioCtxRef.current.close() } catch { /* ignore */ }
      fillerAudioCtxRef.current = null
    }
  }

  const stopProgressTimer = () => {
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }
    setLoadingProgress(0)
  }

  const startProgressTimer = () => {
    stopProgressTimer()
    setLoadingProgress(0)
    let progress = 0
    progressTimerRef.current = window.setInterval(() => {
      // Ease towards ~90% and slow down as it gets higher
      progress += (92 - progress) * 0.02
      setLoadingProgress(Math.min(92, progress))
    }, 100)
  }

  // ── Level metering ──────────────────────────────────────────
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
    stopFillerAudio()
    stopProgressTimer()
    transcribingRef.current = false
  }

  const playWithMeter = async (audioBlob: Blob) => {
    const ac = new AudioContext()
    await ac.resume()
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
    // Stop auto-transcribing chunks when paused
    rec.ondataavailable = async (e) => {
      if (e.data.size) chunksRef.current.push(e.data)
      if (phaseRef.current === 'listening') {
        const ext = extFromMime(recorderMimeRef.current)
        const progressive = new Blob(chunksRef.current, { type: recorderMimeRef.current })
        await transcribeChunk(progressive, ext)
      }
    }
    
    // rec.onstop is now ONLY called when we actually want to submit the audio
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
      fd.append('session_id', sessionId)
      
      // Pass the potentially edited transcript!
      if (transcriptRef.current) {
        fd.append('override_text', transcriptRef.current)
      }

  // Start progress bar during thinking phase
      setVoicePhase('thinking')
      thinkingDoneRef.current = false
      startProgressTimer()

      const finishThinking = () => {
        if (thinkingDoneRef.current) return
        thinkingDoneRef.current = true
        stopFillerAudio()
        stopProgressTimer()
        setLoadingProgress(100)
        window.setTimeout(() => setLoadingProgress(0), 300)
        setVoicePhase('speaking')
      }
      
      try {
        const token = getToken()
        const controller = new AbortController()
        voiceAbortRef.current = controller
        const res = await fetch('/api/voice/process_stream', {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: fd,
          signal: controller.signal,
        })

        if (!res.ok) throw new Error('Voice request failed');
        if (!res.body) throw new Error('No response body');

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullReply = '';

        while (sessionActiveRef.current) {
          const { value, done } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'transcript') {
                   const userMsg: Msg = { role: 'user', content: data.text }
                   setMessages((prev) => [...prev, userMsg])
                   messagesRef.current = [...messagesRef.current, userMsg]
                }
                else if (data.type === 'audio') {
             finishThinking()
                   fullReply += (fullReply ? " " : "") + data.text;
                   setLiveTranscript(fullReply);
                   
                   if (data.audio_base64 && sessionActiveRef.current) {
                     const audioBlob = decodeAudio(String(data.audio_base64), 'audio/wav');
                     await playWithMeter(audioBlob);
                   }
                }
                else if (data.type === 'done') {
             finishThinking()
                   const asstMsg: Msg = { role: 'assistant', content: fullReply }
                   setMessages((prev) => [...prev, asstMsg])
                   messagesRef.current = [...messagesRef.current, asstMsg]
                }
              } catch (e) {
                console.warn("Failed to parse SSE line", e);
              }
            }
          }
        }
        
        if (sessionActiveRef.current) {
          setLoading(false)
          void fetchSessions()
          startVoice()
        }
      } catch (x) {
        stopFillerAudio()
        stopProgressTimer()
        setVoicePhase('idle')
        setVoiceOpen(false)
        sessionActiveRef.current = false
        if (x instanceof DOMException && x.name === 'AbortError') {
          // user cancelled
        } else {
          setErr(x instanceof Error ? x.message : 'voice request failed')
        }
      } finally {
        voiceAbortRef.current = null
        setLoading(false)
      }
    }
    setLoading(true)
    rec.start(700)
    // REMOVED 7.6s AUTO-TIMEOUT to allow natural pauses
  }

  const pauseListeningNow = () => {
    if (!recRef.current || recRef.current.state === 'inactive') return
    // Pause the recorder so we can gather the chunks later when they hit Send
    recRef.current.pause()
    setVoicePhase('reviewing') // Custom state for editing
  }

  const sendListeningNow = () => {
    if (!recRef.current || recRef.current.state === 'inactive') return
    // This will trigger rec.onstop and submit the form
    recRef.current.stop()
    recRef.current = null
  }

  const cancelVoice = () => {
    sessionActiveRef.current = false
    if (voiceAbortRef.current) {
      voiceAbortRef.current.abort()
      voiceAbortRef.current = null
    }
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

  // ── Derive sidebar conversation summary ─────────────────────
  const conversationPreview = useMemo(() => {
    if (messages.length === 0) return null
    // Use the first user message as the thread title
    const firstUser = messages.find((m) => m.role === 'user')
    if (firstUser) {
      const text = firstUser.content
      return text.length > 40 ? text.slice(0, 40) + '…' : text
    }
    return 'Current conversation'
  }, [messages])

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
          onClick={() => void createNewThread()}
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
          {!historyLoaded && sessions.length === 0 ? (
            <div className="flex items-center gap-2 px-2 py-2 text-sm text-zinc-500">
              <span className="flex h-2 w-2 animate-pulse rounded-full bg-zinc-600"></span>
              Loading…
            </div>
          ) : sessions.length > 0 ? (
            sessions.map(s => (
              <button 
                key={s.id}
                onClick={() => setSessionId(s.id)}
                className={`flex w-full items-center gap-3 rounded-lg px-2 py-2 text-sm transition ${s.id === sessionId ? 'bg-zinc-800/80 text-zinc-200' : 'text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-300'}`}
              >
                <MessageSquare size={16} className={`${s.id === sessionId ? 'text-zinc-400' : 'text-zinc-600'} shrink-0`} />
                <span className="truncate text-left">{s.preview}</span>
              </button>
            ))
          ) : conversationPreview && messages.length > 0 ? (
            <button className="flex w-full items-center gap-3 rounded-lg bg-zinc-800/40 px-2 py-2 text-sm text-zinc-300 hover:bg-zinc-800/60 transition">
              <MessageSquare size={16} className="text-zinc-500 shrink-0" />
              <span className="truncate text-left text-zinc-300">{conversationPreview}</span>
            </button>
          ) : (
            <p className="px-2 py-2 text-xs text-zinc-600 italic">No conversations yet</p>
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
        {/* Top Bar (ChatGPT style) */}
        <header className="flex shrink-0 items-center justify-between px-4 py-3 z-20 bg-[#111113]">
          {/* Mobile brand */}
          <div className="flex items-center gap-2 sm:hidden">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-zinc-800 text-zinc-100 shadow-inner">
              <MessageCircle size={14} />
            </div>
            <span className="font-semibold text-white">boliye</span>
          </div>

          {/* Model Selector / Center title */}
          <div className="hidden sm:flex flex-1 items-center justify-start">
            <button className="flex items-center gap-2 rounded-lg px-3 py-2 text-lg font-semibold text-zinc-200 hover:bg-zinc-800/50 transition">
              Boliye-Ji <span className="text-zinc-500 text-sm">▼</span>
            </button>
          </div>

          {/* Right side icons */}
          <div className="flex items-center gap-3">
             <button type="button" className="sm:hidden text-zinc-400 hover:text-zinc-200" onClick={logout}>
               <LogOut size={20} />
             </button>
             <div 
               className="hidden sm:flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-sm font-semibold text-white shadow-sm cursor-pointer hover:opacity-90 transition"
               onClick={logout}
               title="Log out"
             >
               G
             </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto w-full">
          <div className="mx-auto flex w-full max-w-4xl flex-col px-4 pt-4 pb-40 sm:px-6">
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
                        <div className="prose prose-invert max-w-none text-[15px] leading-relaxed text-zinc-300 prose-p:leading-relaxed prose-pre:bg-zinc-800/50 prose-pre:border prose-pre:border-zinc-700/50">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {m.content}
                          </ReactMarkdown>
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
        </div>

        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#111113] via-[#111113] to-transparent pt-10 pb-6 px-4 sm:px-8 pointer-events-none">
          <div className="mx-auto max-w-4xl pointer-events-auto">
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
        {voiceOpen ? (
          <VoiceScreen
            phase={voicePhase}
            transcript={liveTranscript}
            onTranscriptChange={(newText) => {
              setLiveTranscript(newText)
              transcriptRef.current = newText
            }}
            level={voiceLevel}
            onCancel={cancelVoice}
            onPause={pauseListeningNow}
            onSend={sendListeningNow}
            loadingProgress={loadingProgress}
          />
        ) : null}
      </div>
    </div>
  )
}
