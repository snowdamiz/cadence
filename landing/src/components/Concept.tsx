import { BrainCircuit, ShieldCheck, GitCommit } from 'lucide-react'

const pillars = [
  {
    number: '01',
    icon: BrainCircuit,
    color: '#FFAFAF',
    glow: 'rgba(255, 175, 175, 0.1)',
    title: 'Workflow State Machine',
    description:
      'Explicit lifecycle gates with persisted state. Every phase transition is enforced, recorded, and resumable — even after tool restarts or chat session resets.',
    detail: 'scaffold → ideation → execution',
  },
  {
    number: '02',
    icon: ShieldCheck,
    color: '#AFD7FF',
    glow: 'rgba(175, 215, 255, 0.1)',
    title: 'Guarded Skill Router',
    description:
      'Route assertions run before any subskill executes. Out-of-order requests are hard-stopped. The orchestrator enforces legal transitions across the full project lifecycle.',
    detail: 'pre-execution guards on every route',
  },
  {
    number: '03',
    icon: GitCommit,
    color: '#93DBCF',
    glow: 'rgba(147, 219, 207, 0.1)',
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
        <div className="mb-14">
          <p className="section-label mb-3">Core Architecture</p>
          <h2 className="text-3xl sm:text-4xl font-semibold text-white/90 leading-tight max-w-xl">
            Built for the failure modes<br className="hidden sm:block" /> of AI workflows
          </h2>
          <p className="mt-3 text-sm text-white/38 max-w-md leading-relaxed">
            No stable memory. Weak phase boundaries. Unsafe state changes.
            Cadence addresses each one structurally.
          </p>
        </div>

        {/* Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {pillars.map((p) => {
            const Icon = p.icon
            return (
              <div
                key={p.title}
                className="glass-card-hover rounded-xl p-7 group"
                style={{ boxShadow: `inset 0 1px 0 ${p.color}12` }}
              >
                {/* Top row: number + icon */}
                <div className="flex items-center justify-between mb-6">
                  <span
                    className="font-mono text-3xl font-black leading-none"
                    style={{ color: p.color, opacity: 0.25 }}
                  >
                    {p.number}
                  </span>
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center"
                    style={{
                      background: p.glow,
                      border: `1px solid ${p.color}20`,
                    }}
                  >
                    <Icon
                      className="w-4.5 h-4.5"
                      style={{ color: p.color, width: '18px', height: '18px' }}
                      strokeWidth={1.5}
                    />
                  </div>
                </div>

                <h3 className="text-[15px] font-semibold text-white/88 mb-2.5">
                  {p.title}
                </h3>
                <p className="text-[13px] text-white/42 leading-relaxed mb-5">
                  {p.description}
                </p>

                {/* Detail tag */}
                <div
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md font-mono text-[10px]"
                  style={{
                    background: `${p.color}0d`,
                    border: `1px solid ${p.color}18`,
                    color: p.color,
                    opacity: 0.75,
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
