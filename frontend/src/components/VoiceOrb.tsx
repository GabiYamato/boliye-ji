import { useEffect, useState } from 'react'

export type VoicePhase = 'idle' | 'listening' | 'thinking' | 'speaking' | 'reviewing'

export function VoiceOrb({
  phase,
  level = 0.15,
}: {
  phase: VoicePhase
  level?: number
  size?: string // Ignored now but kept for prop compat
}) {
  const active = phase !== 'idle'
  const isSpeaking = phase === 'speaking'
  const isThinking = phase === 'thinking'
  const isListening = phase === 'listening'

  // Smooth level for animation
  const [smoothedLevel, setSmoothedLevel] = useState(level)

  useEffect(() => {
    let animationFrame: number
    const updateLevel = () => {
      setSmoothedLevel((prev) => {
        const diff = level - prev
        const easing = diff > 0 ? 0.2 : 0.1 
        return prev + diff * easing
      })
      animationFrame = requestAnimationFrame(updateLevel)
    }
    animationFrame = requestAnimationFrame(updateLevel)
    return () => cancelAnimationFrame(animationFrame)
  }, [level])

  const intensity = Math.min(smoothedLevel, 1)
  
  return (
    <>
      <style>{`
        @keyframes aura-float-1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(8%, -10%) scale(1.05); }
        }
        @keyframes aura-float-2 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-8%, -12%) scale(1.02); }
        }
        @keyframes aura-float-3 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(3%, 8%) scale(1.08); }
        }
        .aura-anim-1 { animation: aura-float-1 4s ease-in-out infinite; }
        .aura-anim-2 { animation: aura-float-2 5s ease-in-out infinite; }
        .aura-anim-3 { animation: aura-float-3 3.5s ease-in-out infinite; }
      `}</style>

      <div className="absolute bottom-0 left-[-20%] right-[-20%] h-[60vh] pointer-events-none z-0 flex items-end justify-center">
        <div 
          className="relative w-full max-w-5xl h-full"
          style={{
            filter: 'blur(80px)',
            opacity: active ? 0.8 + intensity * 0.2 : 0.0,
            transform: `scaleY(${1 + intensity * 0.3}) translateY(${active ? '10%' : '60%'})`,
            transition: 'opacity 0.6s ease, transform 0.3s ease-out',
          }}
        >
          {/* Deep Blue Base */}
          <div 
            className="absolute bottom-[-10%] left-[-10%] w-[70%] h-[80%] transition-all duration-500 ease-out"
            style={{
              transform: `scale(${isListening ? 1.2 : 1 + intensity * 0.2}) translateX(${isThinking ? '20%' : '0'})`,
            }}
          >
            <div className={`w-full h-full rounded-full bg-[#0070F3] mix-blend-screen ${isThinking || isListening ? 'aura-anim-1' : ''}`} />
          </div>
          
          {/* Right Purple/Pink */}
          <div 
            className="absolute bottom-[-10%] right-[-10%] w-[70%] h-[70%] transition-all duration-500 ease-out"
            style={{
              transform: `scale(${isThinking ? 1.3 : 1 + intensity * 0.3}) translateX(${isListening ? '-20%' : '0'})`,
            }}
          >
            <div className={`w-full h-full rounded-full bg-[#9d4edd] mix-blend-screen ${isThinking || isListening ? 'aura-anim-2' : ''}`} />
          </div>

          {/* Center Cyan Highlight for speaking */}
          <div 
            className="absolute bottom-[0%] left-[15%] right-[15%] h-[60%] transition-all duration-200 ease-out"
            style={{
              transform: `scaleY(${1 + intensity * 1.5}) scaleX(${1 + intensity * 0.4})`,
              opacity: isSpeaking ? 0.8 + intensity * 0.2 : (isListening ? 0.3 : 0),
            }}
          >
            <div className={`w-full h-full rounded-full bg-[#48cae4] mix-blend-screen ${isThinking || isListening ? 'aura-anim-3' : ''}`} />
          </div>
          
          {/* Extra Bright Core for high volume */}
          <div 
            className="absolute bottom-[5%] left-[25%] right-[25%] h-[40%] rounded-full bg-white mix-blend-overlay transition-all duration-150 ease-out"
            style={{
              transform: `scaleY(${1 + intensity * 1.5})`,
              opacity: isSpeaking ? intensity * 0.8 : 0,
            }}
          />
        </div>
      </div>
    </>
  )
}
