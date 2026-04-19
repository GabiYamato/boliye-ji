export type VoicePhase = 'idle' | 'listening' | 'thinking' | 'speaking'

const ring = (phase: VoicePhase) => {
  if (phase === 'listening') return 'animate-pulse shadow-[0_0_40px_rgba(16,163,127,0.55)]'
  if (phase === 'thinking') return 'animate-spin shadow-[0_0_30px_rgba(99,102,241,0.5)]'
  if (phase === 'speaking') return 'animate-bounce shadow-[0_0_36px_rgba(236,72,153,0.45)]'
  return 'opacity-80'
}

export function VoiceOrb({ phase }: { phase: VoicePhase }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`h-16 w-16 rounded-full bg-gradient-to-br from-emerald-400 via-indigo-500 to-fuchsia-500 transition-all duration-300 ${ring(phase)}`}
      />
      <span className="text-xs uppercase tracking-wide text-neutral-400">{phase}</span>
    </div>
  )
}
