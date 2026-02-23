import { useScrollReveal } from '@/hooks/useScrollReveal'
import { BrainCog, ShieldOff, GitBranchPlus } from 'lucide-react'

const PROBLEMS = [
  {
    icon: BrainCog,
    title: 'No memory',
    description:
      'Every new chat starts from zero. Context evaporates between sessions, and the AI re-discovers your project from scratch.',
    accent: 'salmon' as const,
  },
  {
    icon: ShieldOff,
    title: 'No guardrails',
    description:
      'Setup, planning, and execution blur together. There are no phase gates, so the AI skips steps or jumps ahead unpredictably.',
    accent: 'periwinkle' as const,
  },
  {
    icon: GitBranchPlus,
    title: 'No traceability',
    description:
      'AI-generated changes land as giant, unstructured commits — or no commits at all. Rollbacks become archaeology.',
    accent: 'salmon' as const,
  },
]

export function Problem() {
  const ref = useScrollReveal()

  return (
    <section ref={ref} className="relative px-6 py-32">
      <div className="mx-auto max-w-6xl">
        <div className="scroll-reveal mb-16 max-w-2xl">
          <p className="mb-3 text-sm font-medium uppercase tracking-widest text-salmon">
            The problem
          </p>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            AI workflows break in{' '}
            <span className="gradient-text-salmon">predictable ways</span>
          </h2>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {PROBLEMS.map((problem, i) => (
            <div
              key={problem.title}
              className={`scroll-reveal stagger-${i + 1} glass-card-hover p-8`}
            >
              <div
                className={`mb-5 inline-flex rounded-xl p-3 ${
                  problem.accent === 'salmon'
                    ? 'bg-salmon/10 text-salmon'
                    : 'bg-periwinkle/10 text-periwinkle'
                }`}
              >
                <problem.icon size={24} />
              </div>
              <h3 className="mb-3 text-xl font-semibold">{problem.title}</h3>
              <p className="leading-relaxed text-white/50">{problem.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
