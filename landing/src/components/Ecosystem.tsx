import { useScrollReveal } from '@/hooks/useScrollReveal'
import { TOOLS } from '@/lib/constants'
import { PlatformIcon } from './PlatformIcon'

type PillTone = 'salmon' | 'periwinkle'

const PILL_TONES: PillTone[] = [
  'salmon',
  'periwinkle',
  'periwinkle',
  'salmon',
  'salmon',
  'periwinkle',
  'periwinkle',
  'salmon',
]

const RADIAL_OFFSETS = [0, 18, 10, 20, 6, 22, 10, 18]

const VIEWBOX = 640
const CENTER = VIEWBOX / 2
const BASE_ORBIT_RADIUS = 222

const TOOL_LAYOUT = TOOLS.map((tool, i) => {
  const angle = (i / TOOLS.length) * Math.PI * 2 - Math.PI / 2
  const radius = BASE_ORBIT_RADIUS + RADIAL_OFFSETS[i]
  return {
    ...tool,
    tone: PILL_TONES[i],
    angle,
    x: CENTER + radius * Math.cos(angle),
    y: CENTER + radius * Math.sin(angle),
  }
})

function HubVisualization() {
  return (
    <div className="ecosystem-stage relative mx-auto hidden w-full max-w-[44rem] md:block">
      <div className="ecosystem-ambient" aria-hidden="true" />
      <div className="ecosystem-ambient ecosystem-ambient--cool" aria-hidden="true" />

      <div className="ecosystem-wheel absolute inset-0">
        <svg viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`} className="h-full w-full" aria-hidden="true">
          <defs>
            <linearGradient id="ecosystem-spoke-salmon" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgba(255,175,175,0.04)" />
              <stop offset="100%" stopColor="rgba(255,175,175,0.56)" />
            </linearGradient>
            <linearGradient id="ecosystem-spoke-periwinkle" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgba(175,215,255,0.04)" />
              <stop offset="100%" stopColor="rgba(175,215,255,0.56)" />
            </linearGradient>
          </defs>

          <circle cx={CENTER} cy={CENTER} r={238} className="ecosystem-orbit-main" />
          <circle cx={CENTER} cy={CENTER} r={198} className="ecosystem-orbit-secondary" />

          {TOOL_LAYOUT.map((tool, i) => {
            const spokeStroke = tool.tone === 'salmon'
              ? 'url(#ecosystem-spoke-salmon)'
              : 'url(#ecosystem-spoke-periwinkle)'
            const signalClass = tool.tone === 'salmon'
              ? 'ecosystem-signal ecosystem-signal--salmon'
              : 'ecosystem-signal ecosystem-signal--periwinkle'

            return (
              <g key={tool.key}>
                <line
                  x1={CENTER}
                  y1={CENTER}
                  x2={tool.x}
                  y2={tool.y}
                  stroke={spokeStroke}
                  className="ecosystem-spoke"
                />
                <line
                  x1={CENTER}
                  y1={CENTER}
                  x2={tool.x}
                  y2={tool.y}
                  className={signalClass}
                  style={{ animationDelay: `${i * 0.35}s` }}
                />
                <circle
                  cx={tool.x}
                  cy={tool.y}
                  r={6}
                  className={
                    tool.tone === 'salmon'
                      ? 'ecosystem-anchor ecosystem-anchor--salmon'
                      : 'ecosystem-anchor ecosystem-anchor--periwinkle'
                  }
                  style={{ animationDelay: `${i * 0.35}s` }}
                />
              </g>
            )
          })}
        </svg>

        {TOOL_LAYOUT.map((tool, i) => (
          <div
            key={tool.key}
            className="absolute"
            style={{
              left: `${(tool.x / VIEWBOX) * 100}%`,
              top: `${(tool.y / VIEWBOX) * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            <div className="ecosystem-counter-spin">
              <span
                className={
                  tool.tone === 'salmon'
                    ? 'ecosystem-pill ecosystem-pill--salmon'
                    : 'ecosystem-pill ecosystem-pill--periwinkle'
                }
                style={{ animationDelay: `${i * 0.42}s` }}
              >
                <PlatformIcon toolKey={tool.key} className="ecosystem-pill-icon" />
                {tool.name}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="ecosystem-core-wrap">
        <div className="ecosystem-core-ring" />
        <div className="ecosystem-core-ring ecosystem-core-ring--secondary" />
        <div className="ecosystem-core">
          <span className="gradient-text-mixed text-sm font-black tracking-[0.04em] sm:text-base">
            CADENCE
          </span>
          <span className="mt-1 block text-[10px] uppercase tracking-[0.2em] text-white/45">
            Orchestration Hub
          </span>
        </div>
      </div>
    </div>
  )
}

function MobileToolGrid() {
  return (
    <div className="md:hidden">
      <div className="ecosystem-mobile-shell">
        <div className="ecosystem-mobile-core">
          <span className="gradient-text-mixed text-xs font-black tracking-[0.06em]">
            CADENCE
          </span>
        </div>
        <div className="ecosystem-mobile-grid">
          {TOOLS.map((tool, i) => (
            <span
              key={tool.key}
              className={
                PILL_TONES[i] === 'salmon'
                  ? 'ecosystem-mobile-pill ecosystem-mobile-pill--salmon'
                  : 'ecosystem-mobile-pill ecosystem-mobile-pill--periwinkle'
              }
              style={{ animationDelay: `${i * 0.35}s` }}
            >
              <PlatformIcon toolKey={tool.key} className="ecosystem-mobile-pill-icon" />
              {tool.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

export function Ecosystem() {
  const ref = useScrollReveal()

  return (
    <section ref={ref} className="relative px-6 py-32">
      {/* Ambient glows */}
      <div className="glow-salmon left-1/4 top-1/2 h-[400px] w-[400px] -translate-y-1/2" />
      <div className="glow-periwinkle right-1/4 top-1/3 h-[350px] w-[350px]" />

      <div className="relative mx-auto max-w-4xl text-center">
        <div className="scroll-reveal mb-12">
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

        {/* Hub visualization — desktop */}
        <div className="scroll-reveal stagger-2">
          <HubVisualization />
        </div>

        <div className="scroll-reveal stagger-2">
          <MobileToolGrid />
        </div>
      </div>
    </section>
  )
}
