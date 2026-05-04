import { Settings, X, Pause } from 'lucide-react'
import { VoiceOrb, type VoicePhase } from './VoiceOrb'
import { useEffect, useState } from 'react'

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
  const [items, setItems] = useState<{ id: string; text: string; phase: VoicePhase }[]>([])

  useEffect(() => {
    setItems((prev) => {
      let text = transcript
      if (phase === 'thinking') text = 'THINKING'
      else if (phase === 'listening' && !transcript) text = 'Listening...'
      else if (!text) text = ''

      if (!text) return prev

      const newItems = [...prev]
      const lastItem = newItems[newItems.length - 1]

      // Update current text if phase is same, otherwise push new line
      if (lastItem && lastItem.phase === phase) {
        lastItem.text = text
      } else {
        newItems.push({ id: Date.now().toString() + Math.random(), text, phase })
      }

      // Keep up to 4 items in history for the cool fade out effect
      if (newItems.length > 4) {
        return newItems.slice(newItems.length - 4)
      }
      return newItems
    })
  }, [phase, transcript])

  return (
    <>
      <style>{`
        @keyframes text-slide-up {
          from { opacity: 0; transform: translateY(40px) scale(0.95); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-text-slide-up {
          animation: text-slide-up 0.6s cubic-bezier(0.2, 1, 0.2, 1) forwards;
        }
      `}</style>

      <div className="absolute inset-0 z-40 flex flex-col bg-black overflow-hidden rounded-l-3xl shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
        <div className="relative z-10 flex justify-end px-4 py-4 sm:px-6 sm:py-5">
          <button
            type="button"
            aria-label="Voice settings"
            className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white/50 transition hover:bg-white/20 hover:text-white"
          >
            <Settings size={20} />
          </button>
        </div>

        <div className="relative z-10 flex flex-1 flex-col items-center justify-center -mt-32 pointer-events-none">
          <div className="relative w-full max-w-3xl h-[300px] flex flex-col items-center justify-end pb-4">
            {/* Top fade mask so text vanishes smoothly */}
            <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-black to-transparent z-20 pointer-events-none" />
            
            {items.map((item, index) => {
              const distance = items.length - 1 - index
              const isLast = distance === 0

              return (
                <div
                  key={item.id}
                  className="absolute w-full px-8 text-center transition-all duration-700 ease-out flex justify-center"
                  style={{
                    transform: `translateY(${-distance * 80}px) scale(${1 - distance * 0.05})`,
                    opacity: isLast ? 1 : Math.max(0, 0.5 - distance * 0.2),
                    filter: distance > 0 ? `blur(${distance * 2}px)` : 'none',
                    zIndex: 10 - distance,
                  }}
                >
                  <div className="animate-text-slide-up w-full">
                    {item.phase === 'thinking' && isLast ? (
                      <div className="flex items-center justify-center gap-4 text-white/90 drop-shadow-lg">
                        <div className="h-6 w-6 animate-spin rounded-full border-2 border-white/20 border-t-white" />
                        <p className="text-2xl sm:text-3xl lg:text-4xl font-medium tracking-[0.05em]">
                          {item.text}
                        </p>
                      </div>
                    ) : (
                      <p className={`text-2xl sm:text-3xl lg:text-4xl font-medium leading-tight tracking-tight drop-shadow-lg ${isLast ? 'text-white/90' : 'text-white/50'}`}>
                        {item.text}
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <VoiceOrb phase={phase} level={level} />

        <div className="relative z-10 mb-12 flex items-center justify-center gap-10">
          <div className="flex flex-col items-center gap-3">
            <button
              type="button"
              onClick={onStop}
              className="flex h-16 w-16 items-center justify-center rounded-full bg-[#2A3441] text-white transition hover:bg-[#344050]"
              aria-label="Hold"
            >
              <Pause size={24} fill="currentColor" className="text-white" />
            </button>
            <span className="text-xs text-white/70 font-medium">Hold</span>
          </div>

          <div className="flex flex-col items-center gap-3">
            <button
              type="button"
              onClick={onCancel}
              className="flex h-16 w-16 items-center justify-center rounded-full bg-[#E5484D] text-white transition hover:bg-[#F2555A]"
              aria-label="End"
            >
              <X size={28} strokeWidth={2.5} />
            </button>
            <span className="text-xs text-white/70 font-medium">End</span>
          </div>
        </div>
      </div>
    </>
  )
}
