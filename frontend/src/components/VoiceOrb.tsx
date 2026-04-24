import { useMemo } from 'react'

export type VoicePhase = 'idle' | 'listening' | 'thinking' | 'speaking'

const phaseLabel = (phase: VoicePhase) => {
  if (phase === 'listening') return 'listening'
  if (phase === 'thinking') return 'thinking'
  if (phase === 'speaking') return 'speaking'
  return 'idle'
}

const seeded = (n: number) => {
  const x = Math.sin(n * 9127.133) * 43758.5453
  return x - Math.floor(x)
}

export function VoiceOrb({
  phase,
  level = 0.15,
  size = 'h-28 w-28',
}: {
  phase: VoicePhase
  level?: number
  size?: string
}) {
  const amp = Math.max(0.06, Math.min(1, level))
  const scale = 0.94 + amp * 0.2
  const spin = phase === 'thinking' ? 5.6 : phase === 'speaking' ? 9 : 12

  const points = useMemo(() => {
    const out: Array<{ x: number; y: number; r: number; o: number; delay: number; dur: number }> = []
    const count = 880
    for (let i = 0; i < count; i++) {
      const a = 2 * Math.PI * seeded(i + 1)
      const b = Math.acos(2 * seeded(i + 2) - 1)
      const shell = 0.72 + seeded(i + 3) * 0.28
      const x = Math.sin(b) * Math.cos(a) * shell
      const y = Math.sin(b) * Math.sin(a) * shell
      const z = Math.cos(b) * shell
      const perspective = 0.78 + (z + 1) * 0.2
      out.push({
        x: x * 88,
        y: y * 88,
        r: 0.45 + perspective * (0.75 + seeded(i + 5) * 0.8),
        o: 0.14 + perspective * (0.34 + seeded(i + 6) * 0.5),
        delay: seeded(i + 8) * 2.2,
        dur: 1.6 + seeded(i + 7) * 2.8,
      })
    }
    return out
  }, [])

  return (
    <div className="flex flex-col items-center gap-4">
      <div
        className={`relative overflow-hidden rounded-full transition duration-150 ${size}`}
        style={{
          transform: `scale(${scale})`,
          boxShadow: `0 0 ${20 + amp * 32}px rgba(117, 220, 255, ${0.18 + amp * 0.18})`,
          background:
            'radial-gradient(circle at 30% 25%, rgba(153,225,255,0.10), rgba(4,9,15,0.02) 55%, rgba(0,0,0,0) 72%)',
        }}
      >
        <svg
          className="h-full w-full"
          viewBox="-110 -110 220 220"
          aria-label={`voice orb ${phaseLabel(phase)}`}
          role="img"
          style={{
            animation: `orbSpin ${spin}s linear infinite`,
            transformOrigin: 'center',
          }}
        >
          {points.map((p, idx) => (
            <circle
              key={idx}
              cx={p.x}
              cy={p.y}
              r={p.r}
              fill="rgba(230,245,255,0.98)"
              style={{
                opacity: p.o,
                animation: `orbTwinkle ${p.dur}s ease-in-out ${p.delay}s infinite`,
              }}
            />
          ))}
        </svg>
      </div>
      <span className="text-[10px] uppercase tracking-[0.18em] text-[#6d94a8]">{phaseLabel(phase)}</span>
    </div>
  )
}
