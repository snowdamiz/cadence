const tools = [
  { name: 'Claude Code', key: 'claude' },
  { name: 'Codex CLI', key: 'codex' },
  { name: 'Gemini CLI', key: 'gemini' },
  { name: 'GitHub Copilot', key: 'copilot' },
  { name: 'Windsurf', key: 'windsurf' },
  { name: 'OpenCode', key: 'opencode' },
  { name: 'Cursor', key: 'cursor' },
  { name: 'Agents', key: 'agents' },
]

function ToolChip({ name, accent }: { name: string; accent: string }) {
  return (
    <div
      className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full flex-shrink-0 mx-2"
      style={{
        border: `1px solid ${accent}22`,
        background: `${accent}0b`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{ background: accent, opacity: 0.65 }}
      />
      <span className="text-sm font-medium text-white/72 whitespace-nowrap">{name}</span>
    </div>
  )
}

export function Tools() {
  const row1 = [...tools, ...tools]
  const row2 = [...[...tools].reverse(), ...[...tools].reverse()]

  return (
    <section className="relative py-24 overflow-hidden">
      <div className="divider absolute top-0 left-0 right-0" />
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 80% 50% at 50% 50%, rgba(175, 215, 255, 0.04) 0%, transparent 70%)',
        }}
      />

      {/* Header */}
      <div className="px-5 max-w-6xl mx-auto mb-14">
        <p className="section-label mb-3">Ecosystem</p>
        <div className="flex items-end gap-4">
          <h2 className="text-3xl sm:text-4xl font-semibold text-white">
            Works where you already work
          </h2>
          <span className="hidden sm:block font-mono font-black text-white/[0.04] text-7xl leading-none select-none pb-1">
            8
          </span>
        </div>
        <p className="mt-3 text-sm text-white/60 max-w-sm">
          One package. Install to all eight tools at once, or pick and choose.
        </p>
      </div>

      {/* Marquee row 1 — left */}
      <div className="relative mb-3 marquee-mask">
        <div className="flex animate-marquee">
          {row1.map((tool, i) => (
            <ToolChip
              key={`r1-${tool.key}-${i}`}
              name={tool.name}
              accent={i % 2 === 0 ? '#FFAFAF' : '#AFD7FF'}
            />
          ))}
        </div>
      </div>

      {/* Marquee row 2 — right */}
      <div className="relative marquee-mask">
        <div className="flex animate-marquee-reverse">
          {row2.map((tool, i) => (
            <ToolChip
              key={`r2-${tool.key}-${i}`}
              name={tool.name}
              accent={i % 2 === 0 ? '#AFD7FF' : '#FFAFAF'}
            />
          ))}
        </div>
      </div>

      {/* Install CTA */}
      <div className="px-5 max-w-6xl mx-auto mt-14">
        <div className="inline-flex items-center gap-2.5 px-5 py-3 code-block">
          <span className="font-mono text-xs text-white/35">$</span>
          <code className="font-mono text-sm text-white/80">
            npx cadence-skill-installer{' '}
            <span className="text-periwinkle/80">--all --yes</span>
          </code>
        </div>
      </div>
    </section>
  )
}
