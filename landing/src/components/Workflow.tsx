import { useScrollReveal } from '@/hooks/useScrollReveal'
import { Terminal, FolderOpen, Rocket } from 'lucide-react'

const STEPS = [
  {
    icon: Terminal,
    number: '01',
    title: 'Install',
    description:
      'One npx command copies the skill into your AI tool directories. Codex, Claude, Gemini, and five more.',
    accent: 'salmon' as const,
  },
  {
    icon: FolderOpen,
    number: '02',
    title: 'Scaffold',
    description:
      'Start any project and Cadence bootstraps .cadence/, initializes state, runs prerequisite checks, and commits.',
    accent: 'periwinkle' as const,
  },
  {
    icon: Rocket,
    number: '03',
    title: 'Build',
    description:
      'The state machine routes you through ideation, planning, and execution — with checkpoints after every phase.',
    accent: 'salmon' as const,
  },
]

export function Workflow() {
  const ref = useScrollReveal()

  return (
    <section ref={ref} className="relative px-6 py-32">
      <div className="mx-auto max-w-6xl">
        <div className="scroll-reveal mb-16 text-center">
          <p className="mb-3 text-sm font-medium uppercase tracking-widest text-salmon">
            Workflow
          </p>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Install.{' '}
            <span className="gradient-text-salmon">Scaffold.</span>{' '}
            Build.
          </h2>
        </div>

        <div className="relative grid gap-8 md:grid-cols-3">
          {/* Connector line */}
          <div
            className="pointer-events-none absolute left-0 right-0 top-[72px] z-0 hidden h-px md:block"
            style={{
              background:
                'linear-gradient(90deg, transparent, #FFAFAF, #AFD7FF, transparent)',
            }}
          />

          {STEPS.map((step, i) => (
            <div
              key={step.title}
              className={`scroll-reveal stagger-${i + 1} relative z-10 text-center`}
            >
              {/* Number circle */}
              <div
                className={`mx-auto mb-6 flex h-[72px] w-[72px] items-center justify-center rounded-2xl border ${
                  step.accent === 'salmon'
                    ? 'border-salmon/20 bg-salmon/5 text-salmon'
                    : 'border-periwinkle/20 bg-periwinkle/5 text-periwinkle'
                }`}
              >
                <step.icon size={28} />
              </div>
              <span className="mb-2 block font-mono text-xs text-white/30">
                {step.number}
              </span>
              <h3 className="mb-3 text-xl font-semibold">{step.title}</h3>
              <p className="mx-auto max-w-xs leading-relaxed text-white/50">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
