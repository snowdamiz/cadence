import { useScrollReveal } from '@/hooks/useScrollReveal'
import { TOOLS } from '@/lib/constants'

const PILL_STYLES: { color: 'salmon' | 'periwinkle'; speed: 'animate-float' | 'animate-float-slow' }[] = [
  { color: 'salmon', speed: 'animate-float' },
  { color: 'periwinkle', speed: 'animate-float-slow' },
  { color: 'periwinkle', speed: 'animate-float' },
  { color: 'salmon', speed: 'animate-float-slow' },
  { color: 'salmon', speed: 'animate-float' },
  { color: 'periwinkle', speed: 'animate-float-slow' },
  { color: 'periwinkle', speed: 'animate-float' },
  { color: 'salmon', speed: 'animate-float-slow' },
]

export function Ecosystem() {
  const ref = useScrollReveal()

  return (
    <section ref={ref} className="relative px-6 py-32">
      {/* Ambient glows */}
      <div className="glow-salmon left-1/4 top-1/2 h-[400px] w-[400px] -translate-y-1/2" />
      <div className="glow-periwinkle right-1/4 top-1/3 h-[350px] w-[350px]" />

      <div className="relative mx-auto max-w-4xl text-center">
        <div className="scroll-reveal mb-16">
          <p className="mb-3 text-sm font-medium uppercase tracking-widest text-periwinkle">
            Ecosystem
          </p>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Eight tools.{' '}
            <span className="gradient-text-mixed">One skill.</span>
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-white/50">
            Cadence installs into every major AI coding tool. Same workflow, same state, same guarantees — regardless of which tool you use.
          </p>
        </div>

        <div className="scroll-reveal stagger-2 flex flex-wrap items-center justify-center gap-4">
          {TOOLS.map((tool, i) => {
            const style = PILL_STYLES[i]
            return (
              <span
                key={tool.key}
                className={`${style.speed} rounded-full border px-5 py-2.5 font-medium ${
                  style.color === 'salmon'
                    ? 'border-salmon/20 bg-salmon/5 text-salmon'
                    : 'border-periwinkle/20 bg-periwinkle/5 text-periwinkle'
                }`}
                style={{ animationDelay: `${i * 0.4}s` }}
              >
                {tool.name}
              </span>
            )
          })}
        </div>
      </div>
    </section>
  )
}
