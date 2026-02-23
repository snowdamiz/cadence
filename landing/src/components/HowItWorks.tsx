const steps = [
  {
    number: '01',
    color: '#FFFFFF',
    dimColor: 'rgba(255,255,255,0.55)',
    title: 'Install',
    description:
      'Run the installer and select your AI tools from an interactive multi-select TUI. Skill files are written directly to each tool\'s directory.',
    command: 'npx cadence-skill-installer',
  },
  {
    number: '02',
    color: '#FFAFAF',
    dimColor: 'rgba(255,175,175,0.55)',
    title: 'Scaffold',
    description:
      'On first use Cadence creates .cadence/, initializes cadence.json, verifies Python availability, and persists your project configuration.',
    command: 'python3 scripts/run-scaffold-gate.py',
  },
  {
    number: '03',
    color: '#FFAFAF',
    dimColor: 'rgba(255,175,175,0.55)',
    title: 'Ideate',
    description:
      'One-question-at-a-time project definition. Cadence infers a complete domain-agnostic research agenda with entities, topics, and semantic blocks.',
    command: 'python3 scripts/inject-ideation.py',
  },
  {
    number: '04',
    color: '#AFD7FF',
    dimColor: 'rgba(175,215,255,0.55)',
    title: 'Execute',
    description:
      'Phased delivery with guarded milestones, rollup status tracking, and atomic semantic commits after every completed subskill conversation.',
    command: 'python3 scripts/finalize-skill-checkpoint.py',
  },
]

export function HowItWorks() {
  return (
    <section className="relative py-24 px-5 overflow-hidden">
      <div className="divider absolute top-0 left-0 right-0" />
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(255, 175, 175, 0.04) 0%, transparent 70%)',
        }}
      />

      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-16">
          <p className="section-label mb-3">Workflow</p>
          <h2 className="text-3xl sm:text-4xl font-semibold text-white/90">
            Four phases. Enforced.
          </h2>
        </div>

        {/* Steps — 2×2 grid on desktop, stacked on mobile */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {steps.map((step) => (
            <div
              key={step.number}
              className="glass-card-hover rounded-xl p-7"
            >
              {/* Step number */}
              <div
                className="font-mono font-black text-5xl leading-none mb-5 select-none"
                style={{ color: step.color, opacity: 0.15 }}
              >
                {step.number}
              </div>

              <h3
                className="text-base font-semibold mb-2"
                style={{ color: step.color }}
              >
                {step.title}
              </h3>

              <p className="text-[13px] text-white/40 leading-relaxed mb-5">
                {step.description}
              </p>

              {/* Command */}
              <div
                className="flex items-center gap-2 px-3 py-2 rounded-lg font-mono text-[11px]"
                style={{
                  background: 'rgba(6, 6, 16, 0.8)',
                  border: '1px solid rgba(37, 37, 69, 0.55)',
                }}
              >
                <span style={{ color: step.dimColor }}>$</span>
                <code style={{ color: step.dimColor }}>{step.command}</code>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
