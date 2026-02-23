import { useScrollReveal } from '@/hooks/useScrollReveal'
import { Terminal, FolderOpen, Rocket } from 'lucide-react'

function InstallPreview() {
  return (
    <div className="mt-6 overflow-hidden rounded-xl border border-white/[0.06] bg-bg-base/80">
      <div className="flex items-center gap-1.5 border-b border-white/[0.04] px-4 py-2.5">
        <span className="h-2 w-2 rounded-full bg-[#FF5F57]/60" />
        <span className="h-2 w-2 rounded-full bg-[#FEBC2E]/60" />
        <span className="h-2 w-2 rounded-full bg-[#28C840]/60" />
        <span className="ml-2 font-mono text-[10px] text-white/20">terminal</span>
      </div>
      <div className="space-y-1.5 p-4 font-mono text-xs">
        <div>
          <span className="text-periwinkle">$</span>{' '}
          <span className="text-white/50">npx cadence-skill-installer</span>
        </div>
        <div className="text-salmon"> ✓ codex</div>
        <div className="text-salmon"> ✓ claude</div>
        <div className="text-salmon"> ✓ gemini <span className="text-white/25">+5 more</span></div>
        <div className="mt-2 text-periwinkle"> Done — 8 tools configured.</div>
      </div>
    </div>
  )
}

function ScaffoldPreview() {
  return (
    <div className="mt-6 overflow-hidden rounded-xl border border-white/[0.06] bg-bg-base/80 p-4 font-mono text-xs">
      <div className="space-y-1 text-white/35">
        <div>
          <span className="text-periwinkle/70">▸</span>{' '}
          <span className="text-white/50">project/</span>
        </div>
        <div className="pl-4 text-white/20">├─ src/</div>
        <div className="pl-4">
          <span className="text-periwinkle/60">├─</span>{' '}
          <span className="text-periwinkle/80">.cadence/</span>
        </div>
        <div className="pl-8 text-periwinkle/50">├─ cadence.json</div>
        <div className="pl-8 text-white/20">├─ skills/</div>
        <div className="pl-8 text-white/20">└─ checkpoints/</div>
        <div className="mt-3 text-salmon"> ✓ Prerequisites met</div>
        <div className="text-salmon"> ✓ State initialized</div>
        <div className="text-salmon"> ✓ Initial commit pushed</div>
      </div>
    </div>
  )
}

function BuildPreview() {
  const phases = [
    { name: 'Ideation', status: 'done' as const, pct: 100 },
    { name: 'Planning', status: 'active' as const, pct: 66 },
    { name: 'Execution', status: 'pending' as const, pct: 0 },
  ]
  return (
    <div className="mt-6 space-y-2">
      {phases.map(({ name, status, pct }) => (
        <div key={name} className="overflow-hidden rounded-lg border border-white/[0.06] bg-white/[0.02]">
          <div
            className={`flex items-center gap-3 px-4 py-2.5 font-mono text-xs ${
              status === 'done'
                ? 'text-salmon/70'
                : status === 'active'
                ? 'text-periwinkle'
                : 'text-white/20'
            }`}
          >
            <span className={status === 'active' ? 'animate-pulse' : ''}>
              {status === 'done' ? '✓' : status === 'active' ? '●' : '○'}
            </span>
            <span>{name}</span>
            {status === 'active' && (
              <span className="ml-auto text-periwinkle/60">{pct}%</span>
            )}
            {status === 'done' && (
              <span className="ml-auto text-salmon/40">checkpoint saved</span>
            )}
          </div>
          {status === 'active' && (
            <div className="h-0.5 bg-white/[0.03]">
              <div
                className="h-full rounded-full bg-periwinkle/50"
                style={{ width: `${pct}%` }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

const STEPS = [
  {
    icon: Terminal,
    number: '01',
    title: 'Install',
    description: 'One npx command copies the skill into all your AI tool directories.',
    accent: 'salmon' as const,
    Preview: InstallPreview,
  },
  {
    icon: FolderOpen,
    number: '02',
    title: 'Scaffold',
    description: 'Cadence bootstraps .cadence/, initializes state, and commits.',
    accent: 'periwinkle' as const,
    Preview: ScaffoldPreview,
  },
  {
    icon: Rocket,
    number: '03',
    title: 'Build',
    description: 'The state machine routes through phases with atomic checkpoints.',
    accent: 'salmon' as const,
    Preview: BuildPreview,
  },
]

export function Workflow() {
  const ref = useScrollReveal()

  return (
    <section ref={ref} className="relative px-6 py-16 sm:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="scroll-reveal mb-10 sm:mb-16 text-center">
          <p className="mb-3 text-sm font-medium uppercase tracking-widest text-salmon">
            Workflow
          </p>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Install.{' '}
            <span className="gradient-text-salmon">Scaffold.</span>{' '}
            Build.
          </h2>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {STEPS.map((step, i) => (
            <div
              key={step.title}
              className={`scroll-reveal stagger-${i + 1} glass-card flex flex-col p-6`}
            >
              {/* Icon + number */}
              <div className="mb-5 flex items-start justify-between">
                <div
                  className={`flex h-14 w-14 sm:h-[72px] sm:w-[72px] items-center justify-center rounded-2xl border transition-all duration-300 ${
                    step.accent === 'salmon'
                      ? 'border-salmon/20 bg-salmon/5 text-salmon hover:shadow-[0_0_24px_-4px_rgba(255,175,175,0.3)] hover:border-salmon/35'
                      : 'border-periwinkle/20 bg-periwinkle/5 text-periwinkle hover:shadow-[0_0_24px_-4px_rgba(175,215,255,0.3)] hover:border-periwinkle/35'
                  }`}
                >
                  <step.icon size={28} />
                </div>
                <span className="font-mono text-xs text-white/20">{step.number}</span>
              </div>
              <h3 className="mb-2 text-xl font-semibold">{step.title}</h3>
              <p className="text-sm leading-relaxed text-white/50">{step.description}</p>
              <step.Preview />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
