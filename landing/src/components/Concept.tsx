import { BrainCircuit, ShieldCheck, GitCommit } from 'lucide-react'

const pillars = [
  {
    number: '01',
    icon: BrainCircuit,
    color: '#FFAFAF',
    title: 'Workflow State Machine',
    description:
      'Explicit lifecycle gates with persisted state. Every phase transition is enforced, recorded, and resumable — even after tool restarts or chat session resets.',
    detail: 'scaffold → ideation → execution',
  },
  {
    number: '02',
    icon: ShieldCheck,
    color: '#AFD7FF',
    title: 'Guarded Skill Router',
    description:
      'Route assertions run before any subskill executes. Out-of-order requests are hard-stopped. The orchestrator enforces legal transitions across the full project lifecycle.',
    detail: 'pre-execution guards on every route',
  },
  {
    number: '03',
    icon: GitCommit,
    color: '#93DBCF',
    title: 'Atomic Git Checkpoints',
    description:
      'Semantic batch commits close every successful subskill conversation. Files are classified, grouped, and committed with conventional messages — rollback-safe by design.',
    detail: 'feat(scope): checkpoint message',
  },
]

export function Concept() {
  return (
    <section className="relative py-24 px-5 overflow-hidden">
      <div className="divider absolute top-0 left-0 right-0" />

      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-16">
          <p className="section-label mb-3">Core Architecture</p>
          <h2 className="text-3xl sm:text-4xl font-semibold text-white leading-tight max-w-xl">
            Built for the failure modes<br className="hidden sm:block" /> of AI workflows
          </h2>
          <p className="mt-4 text-sm text-white/60 max-w-md leading-relaxed">
            No stable memory. Weak phase boundaries. Unsafe state changes.
            Cadence addresses each one structurally.
          </p>
        </div>

        {/* Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-x-12 gap-y-14">
          {pillars.map((p) => {
            const Icon = p.icon
            return (
              <div key={p.title} className="relative overflow-hidden">
                {/* Giant background number */}
                <span
                  className="absolute -top-6 -right-1 font-mono font-black select-none pointer-events-none leading-none"
                  style={{ fontSize: '9rem', color: p.color, opacity: 0.05 }}
                >
                  {p.number}
                </span>

                {/* Colored top accent bar */}
                <div
                  className="h-[2px] mb-8 rounded-full"
                  style={{
                    background: `linear-gradient(to right, ${p.color}cc, ${p.color}00)`,
                  }}
                />

                {/* Icon + number row */}
                <div className="flex items-center gap-3 mb-6">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{
                      background: `${p.color}18`,
                      border: `1px solid ${p.color}35`,
                    }}
                  >
                    <Icon
                      className="w-4 h-4"
                      style={{ color: p.color }}
                      strokeWidth={1.5}
                    />
                  </div>
                  <span
                    className="font-mono text-[11px] font-bold tracking-[0.2em]"
                    style={{ color: p.color, opacity: 0.8 }}
                  >
                    {p.number}
                  </span>
                </div>

                <h3 className="text-base font-semibold text-white mb-3">
                  {p.title}
                </h3>
                <p className="text-sm text-white/60 leading-relaxed mb-6">
                  {p.description}
                </p>

                {/* Detail tag */}
                <div
                  className="inline-flex items-center px-3 py-1.5 rounded-lg font-mono text-[10px] font-medium"
                  style={{
                    background: `${p.color}12`,
                    border: `1px solid ${p.color}28`,
                    color: p.color,
                  }}
                >
                  {p.detail}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
