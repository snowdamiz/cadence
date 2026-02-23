import { useScrollReveal } from '@/hooks/useScrollReveal'
import { Workflow, ShieldCheck, GitCommitHorizontal } from 'lucide-react'

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

        <div className="grid gap-6 lg:grid-cols-3">
          {PILLARS.map((pillar, i) => (
            <div
              key={pillar.title}
              className={`scroll-reveal stagger-${i + 1} glass-card flex flex-col overflow-hidden`}
            >
              <div className="flex-1 p-8">
                <div
                  className={`mb-5 inline-flex rounded-xl p-3 ${
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
              {/* Code preview */}
              <div className="border-t border-white/[0.06] bg-bg-base/60 p-5">
                <pre className="overflow-x-auto font-mono text-xs leading-relaxed text-white/40">
                  {pillar.code}
                </pre>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
