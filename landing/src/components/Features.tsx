import {
  Database,
  Route,
  Puzzle,
  BookOpenCheck,
  RefreshCw,
  FileSearch,
} from 'lucide-react'

const JSON_PREVIEW = `{
  "phase": "ideation",
  "project": "my-app",
  "checkpoint": 3,
  "tools": ["claude", "codex"]
}`

const PHASE_FLOW = `scaffold → ideation → execution
    ✔           ✔           ·`

const features = [
  {
    icon: Database,
    title: 'Cross-session memory',
    description:
      '.cadence/cadence.json persists state across tool restarts, chat resets, and model switches. Pick up exactly where you left off.',
    featured: true,
    accent: '#FFAFAF',
    preview: JSON_PREVIEW,
  },
  {
    icon: Route,
    title: 'Phase-guarded routing',
    description:
      'Scaffold before ideation, ideation before execution. Hard stops on out-of-order requests prevent accidental phase skipping.',
    featured: true,
    accent: '#AFD7FF',
    preview: PHASE_FLOW,
  },
  {
    icon: Puzzle,
    title: 'Multi-tool ecosystem',
    description: 'One installer, eight AI tools. Install to all in a single command.',
    accent: '#FFAFAF',
  },
  {
    icon: BookOpenCheck,
    title: 'Structured research agenda',
    description:
      'Ideation produces a normalized agenda with entity registry, topic index, and semantic blocks.',
    accent: '#AFD7FF',
  },
  {
    icon: RefreshCw,
    title: 'Idempotent scaffolding',
    description: 'Scaffold runs are always safe to repeat. Existing state is detected and preserved.',
    accent: '#FFAFAF',
  },
  {
    icon: FileSearch,
    title: 'Audit traceability',
    description:
      'Every state change is committed with a conventional message. Scope and checkpoint are always explicit.',
    accent: '#AFD7FF',
  },
]

export function Features() {
  return (
    <section className="relative py-24 px-5 overflow-hidden">
      <div className="divider absolute top-0 left-0 right-0" />

      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-14">
          <p className="section-label mb-3">Capabilities</p>
          <h2 className="text-3xl sm:text-4xl font-semibold text-white">
            What Cadence does for you
          </h2>
        </div>

        {/* Featured features — bento cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-16">
          {features
            .filter((f) => f.featured)
            .map((f) => {
              const Icon = f.icon
              return (
                <div
                  key={f.title}
                  className="relative rounded-2xl overflow-hidden flex flex-col"
                  style={{
                    background: 'rgba(10, 10, 22, 0.95)',
                    border: `1px solid ${f.accent}20`,
                  }}
                >
                  {/* Inner gradient glow at top */}
                  <div
                    className="absolute top-0 left-0 right-0 h-56 pointer-events-none"
                    style={{
                      background: `radial-gradient(ellipse at top left, ${f.accent}14 0%, transparent 65%)`,
                    }}
                  />

                  <div className="relative z-10 p-8 flex flex-col h-full">
                    <div
                      className="w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-xl mb-6"
                      style={{
                        background: `${f.accent}18`,
                        border: `1px solid ${f.accent}38`,
                      }}
                    >
                      <Icon
                        className="w-5 h-5"
                        style={{ color: f.accent }}
                        strokeWidth={1.5}
                      />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2.5">
                      {f.title}
                    </h3>
                    <p className="text-sm text-white/60 leading-relaxed mb-6">
                      {f.description}
                    </p>
                    <div className="mt-auto code-block rounded-xl px-5 py-4 overflow-x-auto">
                      <pre
                        className="font-mono text-[11px] leading-relaxed whitespace-pre"
                        style={{ color: f.accent, opacity: 0.9 }}
                      >
                        {f.preview}
                      </pre>
                    </div>
                  </div>
                </div>
              )
            })}
        </div>

        {/* Secondary features — open 4-column strip */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-10 border-t border-white/[0.06] pt-12">
          {features
            .filter((f) => !f.featured)
            .map((f) => {
              const Icon = f.icon
              return (
                <div key={f.title}>
                  <Icon
                    className="w-4 h-4 mb-4"
                    style={{ color: f.accent }}
                    strokeWidth={1.5}
                  />
                  <h3 className="text-[14px] font-semibold text-white/90 mb-2">
                    {f.title}
                  </h3>
                  <p className="text-xs text-white/55 leading-relaxed">
                    {f.description}
                  </p>
                </div>
              )
            })}
        </div>
      </div>
    </section>
  )
}
