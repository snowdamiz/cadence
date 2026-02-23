import { useScrollReveal } from '@/hooks/useScrollReveal'
import { Workflow, ShieldCheck, GitCommitHorizontal } from 'lucide-react'

const PHASES = [
  { label: 'Setup', color: 'neutral' as const },
  { label: 'Ideator', color: 'periwinkle' as const },
  { label: 'Planner', color: 'periwinkle' as const },
  { label: 'Executor', color: 'salmon' as const },
]

function PhaseFlow() {
  return (
    <div className="scroll-reveal stagger-1 mb-14 flex items-center justify-center gap-0 overflow-x-auto pb-2">
      {PHASES.map((phase, i) => (
        <div key={phase.label} className="flex shrink-0 items-center">
          <div
            className={`flex h-10 items-center rounded-xl border px-5 font-mono text-sm font-medium ${
              phase.color === 'periwinkle'
                ? 'border-periwinkle/30 bg-periwinkle/10 text-periwinkle'
                : phase.color === 'salmon'
                ? 'border-salmon/30 bg-salmon/10 text-salmon'
                : 'border-white/10 bg-white/[0.04] text-white/40'
            }`}
          >
            <span className="mr-2 font-sans text-[10px] text-white/20">0{i + 1}</span>
            {phase.label}
          </div>
          {i < PHASES.length - 1 && (
            <div className="flex shrink-0 items-center gap-0">
              <div
                className="h-px w-8"
                style={{
                  background: 'linear-gradient(90deg, rgba(175,215,255,0.25), rgba(255,175,175,0.25))',
                }}
              />
              <svg width="6" height="10" viewBox="0 0 6 10" fill="none" aria-hidden="true">
                <path d="M0 0L6 5L0 10V0Z" fill="rgba(255,175,175,0.35)" />
              </svg>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

const PILLARS = [
  {
    icon: Workflow,
    title: 'Workflow State Machine',
    description:
      'Persistent state in .cadence/cadence.json drives deterministic routing. Every phase transition is computed, never guessed.',
    accent: 'salmon' as const,
    code: `{
  "workflow": {
    "next_route": {
      "skill_name": "ideator",
      "status": "pending"
    },
    "completion_pct": 66
  }
}`,
  },
  {
    icon: ShieldCheck,
    title: 'Guarded Skill Router',
    description:
      'Route assertions block out-of-order execution. The AI can only invoke the skill that the state machine has queued.',
    accent: 'periwinkle' as const,
    code: `$ assert-workflow-route.py \\
    --skill ideator

✓ Route matches: ideator
  Proceeding with execution...`,
  },
  {
    icon: GitCommitHorizontal,
    title: 'Atomic Git Checkpoints',
    description:
      'After each skill completes, changes are batched into small, semantically-grouped commits with conventional messages.',
    accent: 'salmon' as const,
    code: `cadence(ideator): persist ideation
  payload [cadence-state]
cadence(ideator): update skill
  instructions [skill-instructions]
cadence(ideator): save research
  scripts [scripts 1/2]`,
  },
]

export function Architecture() {
  const ref = useScrollReveal()

  return (
    <section ref={ref} id="architecture" className="relative px-6 py-32">
      {/* Ambient glow */}
      <div className="glow-periwinkle left-1/2 top-0 h-[600px] w-[600px] -translate-x-1/2" />

      <div className="relative mx-auto max-w-6xl">
        <div className="scroll-reveal mb-16 text-center">
          <p className="mb-3 text-sm font-medium uppercase tracking-widest text-periwinkle">
            Architecture
          </p>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Three pillars,{' '}
            <span className="gradient-text-periwinkle">enforced by default</span>
          </h2>
        </div>

        <PhaseFlow />

        <div className="grid gap-6 lg:grid-cols-3">
          {PILLARS.map((pillar, i) => (
            <div
              key={pillar.title}
              className={`scroll-reveal stagger-${i + 1} glass-card flex flex-col overflow-hidden`}
            >
              <div className="flex-1 p-8">
                <div
                  className={`mb-5 w-fit rounded-xl p-3 ${
                    pillar.accent === 'salmon'
                      ? 'bg-salmon/10 text-salmon'
                      : 'bg-periwinkle/10 text-periwinkle'
                  }`}
                >
                  <pillar.icon size={24} />
                </div>
                <h3 className="mb-3 text-xl font-semibold">{pillar.title}</h3>
                <p className="leading-relaxed text-white/50">{pillar.description}</p>
              </div>
              {/* Code preview — fixed height so all three bottom sections align */}
              <div className="relative border-t border-white/[0.06] bg-bg-base/60 p-5" style={{ height: 160 }}>
                <pre className="overflow-hidden font-mono text-xs leading-relaxed text-white/40" style={{ height: '100%' }}>
                  {pillar.code}
                </pre>
                {/* Fade clipped content */}
                <div
                  className="pointer-events-none absolute inset-x-0 bottom-0 h-10"
                  style={{ background: 'linear-gradient(to top, rgba(7,7,14,0.9), transparent)' }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
