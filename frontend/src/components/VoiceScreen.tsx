import { Settings, X, Mic } from 'lucide-react'
import { VoiceOrb, type VoicePhase } from './VoiceOrb'

export function VoiceScreen({
  phase,
  transcript,
  level,
  onCancel,
  onStop,
}: {
  phase: VoicePhase
  transcript: string
  level: number
  onCancel: () => void
  onStop: () => void
}) {
  const title =
    phase === 'listening' ? 'Say something...' : phase === 'thinking' ? 'Thinking...' : 'Speaking...'

  return (
    <div className="fixed inset-0 z-40 flex flex-col bg-[#161618] px-4 py-4 sm:px-6 sm:py-5">
      <div className="relative flex justify-end">
        <button
          type="button"
          aria-label="Voice settings"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-800 text-zinc-400 transition hover:bg-zinc-700 hover:text-zinc-200"
        >
          <Settings size={20} />
        </button>
      </div>

      <div className="relative flex flex-1 flex-col items-center justify-center">
        <VoiceOrb phase={phase} level={level} size="h-44 w-44 sm:h-48 sm:w-48" />
        <p className="mt-16 text-center text-3xl font-medium tracking-tight text-white">{title}</p>
        <p className="mt-3 min-h-8 max-w-2xl px-8 text-center text-base leading-relaxed text-zinc-400">
          {transcript}
        </p>
      </div>

      <div className="relative mb-6 flex items-center justify-center gap-6">
        <button
          type="button"
          onClick={onCancel}
          className="flex h-14 w-14 items-center justify-center rounded-full bg-[#202022] text-zinc-400 transition hover:bg-[#2A2A2C] hover:text-white"
          aria-label="Cancel voice mode"
        >
          <X size={24} />
        </button>
        <button
          type="button"
          onClick={onStop}
          className="flex h-14 w-14 items-center justify-center rounded-full bg-white text-zinc-900 transition hover:bg-zinc-200"
          aria-label="Stop listening"
        >
          <Mic size={24} className="text-zinc-900" />
        </button>
      </div>
    </div>
  )
}
