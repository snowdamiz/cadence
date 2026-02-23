const tools = [
  { name: 'Codex', key: 'codex', flag: '--tools codex' },
  { name: 'Claude', key: 'claude', flag: '--tools claude' },
  { name: 'Gemini', key: 'gemini', flag: '--tools gemini' },
  { name: 'Copilot', key: 'copilot', flag: '--tools copilot' },
  { name: 'GitHub Copilot', key: 'github-copilot', flag: '--tools github-copilot' },
  { name: 'Windsurf', key: 'windsurf', flag: '--tools windsurf' },
  { name: 'OpenCode', key: 'opencode', flag: '--tools opencode' },
  { name: 'Agents', key: 'agents', flag: '--tools agents' },
]

function ToolMonogram({ name, color }: { name: string; color: string }) {
  const initials = name
    .split(/[\s-]/)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
  return (
    <span
      className="font-mono font-bold text-[13px] transition-colors"
      style={{ color }}
    >
      {initials}
    </span>
  )
}

export function Tools() {
  return (
    <section className="relative py-24 px-5 overflow-hidden">
      <div className="divider absolute top-0 left-0 right-0" />
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 80% 50% at 50% 50%, rgba(175, 215, 255, 0.025) 0%, transparent 70%)',
        }}
      />

      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-14">
          <p className="section-label mb-3">Ecosystem</p>
          <h2 className="text-3xl sm:text-4xl font-semibold text-white/90">
            Works where you already work
          </h2>
          <p className="mt-3 text-sm text-white/38 max-w-sm">
            One package. Install to all eight tools at once, or pick and choose.
          </p>
        </div>

        {/* Tool grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {tools.map((tool, i) => {
            const color = i % 2 === 0 ? '#FFAFAF' : '#AFD7FF'
            return (
              <div
                key={tool.key}
                className="group glass-card-hover rounded-xl p-5 flex flex-col items-center gap-3 cursor-default"
              >
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center"
                  style={{
                    background: `${color}0e`,
                    border: `1px solid ${color}1a`,
                  }}
                >
                  <ToolMonogram name={tool.name} color={`${color}90`} />
                </div>
                <div className="text-center">
                  <p className="text-[12px] font-medium text-white/65 group-hover:text-white/85 transition-colors">
                    {tool.name}
                  </p>
                  <p className="mt-0.5 font-mono text-[10px] text-white/22">
                    {tool.flag}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        {/* Install all CTA */}
        <div className="flex justify-center sm:justify-start">
          <div className="inline-flex items-center gap-2.5 px-5 py-3 code-block">
            <span className="font-mono text-xs text-white/22">$</span>
            <code className="font-mono text-sm text-white/65">
              npx cadence-skill-installer{' '}
              <span className="text-periwinkle/70">--all --yes</span>
            </code>
          </div>
        </div>
      </div>
    </section>
  )
}
