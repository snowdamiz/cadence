import { useScrollReveal } from '@/hooks/useScrollReveal'
import { BrainCog, ShieldOff, GitBranchPlus } from 'lucide-react'

function NoMemoryVisual() {
  return (
    <div className="mt-6 space-y-2 font-mono text-xs">
      <div className="flex items-center gap-3 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2.5">
        <div className="h-4 w-4 shrink-0 rounded-full bg-salmon/20" />
        <div className="flex-1 space-y-1">
          <div className="h-1.5 w-3/4 rounded bg-white/15" />
          <div className="h-1.5 w-1/2 rounded bg-white/10" />
        </div>
        <span className="text-[10px] text-white/20">session 1</span>
      </div>
      <div className="flex justify-center">
        <div className="relative h-5 w-px border-l border-dashed border-white/10">
          <div className="absolute -bottom-1 -left-[3px] h-1.5 w-1.5 rounded-full bg-salmon/30" />
        </div>
      </div>
      <div className="flex items-center gap-3 rounded-lg border border-white/[0.04] bg-white/[0.01] px-3 py-2.5 opacity-40">
        <div className="h-4 w-4 shrink-0 rounded-full bg-white/10" />
        <div className="flex-1 space-y-1">
          <div className="h-1.5 w-1/4 rounded bg-white/10" />
        </div>
        <span className="text-[10px] text-white/20">session 2</span>
      </div>
      <div className="rounded-md border border-salmon/15 bg-salmon/5 px-3 py-1.5 text-center text-[10px] text-salmon/60">
        context evaporated
      </div>
    </div>
  )
}

function NoGuardrailsVisual() {
  const phases = ['Execution', 'Setup', 'Planning', 'Ideation']
  const offsets = [0, 20, 8, 32]
  return (
    <div className="mt-6 space-y-1.5 font-mono text-xs">
      {phases.map((phase, i) => (
        <div
          key={phase}
          className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2"
          style={{ marginLeft: offsets[i] }}
        >
          <span className="text-[10px] text-white/20">{i + 1}</span>
          <span className="text-white/40">{phase}</span>
          {i === 0 && (
            <span className="ml-auto rounded border border-periwinkle/20 px-1.5 py-0.5 text-[10px] text-periwinkle/60">
              out of order
            </span>
          )}
        </div>
      ))}
    </div>
  )
}

function NoTraceabilityVisual() {
  return (
    <div className="mt-6 space-y-2 font-mono text-xs">
      <div className="flex items-center gap-2 rounded-lg border border-salmon/15 bg-salmon/5 px-3 py-2">
        <span className="text-salmon/50">●</span>
        <span className="flex-1 truncate text-white/30">a1b2c3d feat: implement everything</span>
        <span className="shrink-0 rounded border border-salmon/20 bg-salmon/10 px-2 py-0.5 text-[10px] text-salmon/70">
          +2847 lines
        </span>
      </div>
      <div className="flex items-center justify-center gap-2 py-0.5 text-[10px] text-white/20">
        <div className="h-px flex-1 bg-white/[0.04]" />
        vs
        <div className="h-px flex-1 bg-white/[0.04]" />
      </div>
      {[
        { msg: 'cadence(ideator): persist state', lines: '+12' },
        { msg: 'cadence(planner): save plan', lines: '+8' },
        { msg: 'cadence(executor): run build', lines: '+31' },
      ].map(({ msg, lines }) => (
        <div key={msg} className="flex items-center gap-2 rounded-lg border border-periwinkle/10 bg-periwinkle/[0.04] px-3 py-1.5">
          <span className="text-periwinkle/50">●</span>
          <span className="flex-1 truncate text-white/30">{msg}</span>
          <span className="shrink-0 text-[10px] text-white/20">{lines}</span>
        </div>
      ))}
    </div>
  )
}

const PROBLEMS = [
  {
    icon: BrainCog,
    title: 'No memory',
    description: 'Every new chat starts from zero. Context evaporates between sessions.',
    accent: 'salmon' as const,
    Visual: NoMemoryVisual,
  },
  {
    icon: ShieldOff,
    title: 'No guardrails',
    description: 'Setup, planning, and execution blur together. The AI skips steps or jumps ahead unpredictably.',
    accent: 'periwinkle' as const,
    Visual: NoGuardrailsVisual,
  },
  {
    icon: GitBranchPlus,
    title: 'No traceability',
    description: 'AI changes land as giant unstructured commits — or no commits at all.',
    accent: 'salmon' as const,
    Visual: NoTraceabilityVisual,
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
              className={`scroll-reveal stagger-${i + 1} glass-card-hover flex flex-col p-7`}
            >
              <div
                className={`mb-5 w-fit rounded-xl p-3 ${
                  problem.accent === 'salmon'
                    ? 'bg-salmon/10 text-salmon'
                    : 'bg-periwinkle/10 text-periwinkle'
                }`}
              >
                <problem.icon size={22} />
              </div>
              <h3 className="mb-2 text-lg font-semibold">{problem.title}</h3>
              <p className="text-sm leading-relaxed text-white/45">{problem.description}</p>
              <problem.Visual />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
