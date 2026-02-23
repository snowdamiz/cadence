const steps = [
  {
    color: '#FFFFFF',
    dimColor: 'rgba(255,255,255,0.6)',
    title: 'Install',
    description:
      "Run the installer and select your AI tools from an interactive multi-select TUI. Skill files are written directly to each tool's directory.",
    command: 'npx cadence-skill-installer',
  },
  {
    color: '#FFAFAF',
    dimColor: 'rgba(255,175,175,0.7)',
    title: 'Scaffold',
    description:
      'On first use Cadence creates .cadence/, initializes cadence.json, verifies Python availability, and persists your project configuration.',
    command: 'python3 scripts/run-scaffold-gate.py',
  },
  {
    color: '#FFAFAF',
    dimColor: 'rgba(255,175,175,0.7)',
    title: 'Ideate',
    description:
      'One-question-at-a-time project definition. Cadence infers a complete domain-agnostic research agenda with entities, topics, and semantic blocks.',
    command: 'python3 scripts/inject-ideation.py',
  },
  {
    color: '#AFD7FF',
    dimColor: 'rgba(175,215,255,0.7)',
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
            'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(255, 175, 175, 0.05) 0%, transparent 70%)',
        }}
      />

      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-16">
          <p className="section-label mb-3">Workflow</p>
          <h2 className="text-3xl sm:text-4xl font-semibold text-white">
            Four phases. Enforced.
          </h2>
        </div>

        {/* Steps — 2×2 grid on desktop, vertical stack on mobile */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {steps.map((step, i) => (
            <div
              key={step.title}
              className="relative overflow-hidden rounded-2xl p-8"
              style={{
                background: `${step.color}05`,
                border: `1px solid ${step.color}12`,
              }}
            >
              {/* Giant background step number */}
              <span
                className="absolute right-4 bottom-2 font-mono font-black select-none pointer-events-none leading-none"
                style={{ fontSize: '7rem', color: step.color, opacity: 0.06 }}
              >
                {String(i + 1).padStart(2, '0')}
              </span>

              {/* Step number badge */}
              <div className="mb-6">
                <span
                  className="font-mono text-[11px] font-bold tracking-[0.2em]"
                  style={{ color: step.color, opacity: 0.65 }}
                >
                  STEP {String(i + 1).padStart(2, '0')}
                </span>
              </div>

              <h3
                className="text-xl font-bold mb-3"
                style={{ color: step.color }}
              >
                {step.title}
              </h3>
              <p className="text-sm text-white/60 leading-relaxed mb-6">
                {step.description}
              </p>
              <div
                className="relative z-10 inline-flex items-center gap-2 px-3.5 py-2.5 rounded-lg font-mono text-xs"
                style={{
                  background: 'rgba(5, 5, 14, 0.9)',
                  border: `1px solid ${step.color}22`,
                }}
              >
                <span style={{ color: step.dimColor, opacity: 0.6 }}>$</span>
                <code style={{ color: step.dimColor }}>{step.command}</code>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
