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
    previewLang: 'json',
  },
  {
    icon: Route,
    title: 'Phase-guarded routing',
    description:
      'Scaffold before ideation, ideation before execution. Hard stops on out-of-order requests prevent accidental phase skipping.',
    featured: true,
    accent: '#AFD7FF',
    preview: PHASE_FLOW,
    previewLang: 'text',
  },
  {
    icon: Puzzle,
    title: 'Multi-tool ecosystem',
    description:
      'One installer, eight AI tools. Install to all in a single command.',
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
    description:
      'Scaffold runs are always safe to repeat. Existing state is detected and preserved.',
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
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 80% 50% at 50% 100%, rgba(175, 215, 255, 0.04) 0%, transparent 70%)',
        }}
      />
      <div className="divider absolute top-0 left-0 right-0" />

      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-14">
          <p className="section-label mb-3">Capabilities</p>
          <h2 className="text-3xl sm:text-4xl font-semibold text-white/90">
            What Cadence does for you
          </h2>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 auto-rows-auto">
          {/* Featured cards (col-span-2) */}
          {features
            .filter((f) => f.featured)
            .map((f) => {
              const Icon = f.icon
              return (
                <div
                  key={f.title}
                  className="lg:col-span-2 glass-card-hover rounded-xl p-7 flex flex-col"
                >
                  <div
                    className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-lg mb-5"
                    style={{
                      background: `${f.accent}10`,
                      border: `1px solid ${f.accent}1c`,
                    }}
                  >
                    <Icon
                      style={{ color: f.accent, width: '17px', height: '17px' }}
                      strokeWidth={1.5}
                    />
                  </div>
                  <h3 className="text-[15px] font-semibold text-white/88 mb-2">
                    {f.title}
                  </h3>
                  <p className="text-[13px] text-white/40 leading-relaxed mb-5">
                    {f.description}
                  </p>
                  {/* Code preview */}
                  <div className="mt-auto code-block rounded-lg px-4 py-3 overflow-x-auto">
                    <pre
                      className="font-mono text-[11px] leading-relaxed whitespace-pre"
                      style={{ color: f.accent, opacity: 0.7 }}
                    >
                      {f.preview}
                    </pre>
                  </div>
                </div>
              )
            })}

          {/* Regular cards (col-span-1) */}
          {features
            .filter((f) => !f.featured)
            .map((f) => {
              const Icon = f.icon
              return (
                <div
                  key={f.title}
                  className="glass-card-hover rounded-xl p-6 flex flex-col"
                >
                  <div
                    className="w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-md mb-4"
                    style={{
                      background: `${f.accent}0f`,
                      border: `1px solid ${f.accent}18`,
                    }}
                  >
                    <Icon
                      style={{ color: f.accent, width: '15px', height: '15px' }}
                      strokeWidth={1.5}
                    />
                  </div>
                  <h3 className="text-[13px] font-semibold text-white/82 mb-2">
                    {f.title}
                  </h3>
                  <p className="text-[12px] text-white/38 leading-relaxed">
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
