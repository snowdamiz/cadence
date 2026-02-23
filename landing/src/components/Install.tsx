import { useState } from 'react'
import { Copy, Check, Github, ExternalLink } from 'lucide-react'

const commands = [
  {
    label: 'Interactive',
    code: 'npx cadence-skill-installer',
    comment: '# Launch the TUI tool selector',
    featured: true,
  },
  {
    label: 'All tools',
    code: 'npx cadence-skill-installer --all --yes',
    comment: '# Non-interactive — installs to all supported tools',
    featured: false,
  },
  {
    label: 'Specific tools',
    code: 'npx cadence-skill-installer --tools codex,claude --yes',
    comment: '# Choose which tools to install to',
    featured: false,
  },
]

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="flex-shrink-0 p-1.5 rounded text-white/22 hover:text-white/55 hover:bg-white/[0.04] transition-all"
      title="Copy"
    >
      {copied ? (
        <Check className="w-3.5 h-3.5 text-green-400" />
      ) : (
        <Copy className="w-3.5 h-3.5" />
      )}
    </button>
  )
}

export function Install() {
  return (
    <section className="relative py-24 px-5 overflow-hidden">
      <div className="divider absolute top-0 left-0 right-0" />
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 70% 60% at 50% 100%, rgba(255, 175, 175, 0.05) 0%, transparent 70%)',
        }}
      />

      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <p className="section-label mb-3">Get Started</p>
          <h2 className="text-3xl sm:text-4xl font-semibold text-white/90 mb-3">
            One command to install
          </h2>
          <p className="text-sm text-white/38 leading-relaxed max-w-sm">
            Copies skill files into your selected AI tool directories. No
            config, no accounts, no tokens.
          </p>
        </div>

        {/* Featured command */}
        <div className="mb-4">
          {commands
            .filter((c) => c.featured)
            .map((cmd) => (
              <div
                key={cmd.label}
                className="gradient-border-card rounded-xl overflow-hidden"
              >
                <div className="glass-card px-5 py-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="section-label text-[10px]">{cmd.label}</span>
                    <CopyButton text={cmd.code} />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-white/20">$</span>
                    <code className="font-mono text-sm text-white/80">
                      {cmd.code}
                    </code>
                  </div>
                  <p className="mt-2 font-mono text-[11px] text-white/25">
                    {cmd.comment}
                  </p>
                </div>
              </div>
            ))}
        </div>

        {/* Other commands */}
        <div className="flex flex-col gap-2.5 mb-12">
          {commands
            .filter((c) => !c.featured)
            .map((cmd) => (
              <div
                key={cmd.label}
                className="glass-card-hover rounded-lg px-5 py-3.5"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-mono text-xs text-white/18 flex-shrink-0">$</span>
                    <code className="font-mono text-[13px] text-white/60 truncate">
                      {cmd.code}
                    </code>
                  </div>
                  <CopyButton text={cmd.code} />
                </div>
                <p className="mt-1.5 font-mono text-[11px] text-white/22 pl-4">
                  {cmd.comment}
                </p>
              </div>
            ))}
        </div>

        {/* Links */}
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-3">
          <a
            href="https://github.com/snowdamiz/cadence"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-[13px] text-white/40 hover:text-white/70 transition-colors"
          >
            <Github className="w-3.5 h-3.5" />
            GitHub
          </a>
          <span className="text-white/12">·</span>
          <a
            href="https://www.npmjs.com/package/cadence-skill-installer"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-[13px] text-white/40 hover:text-white/70 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            npm
          </a>
          <span className="text-white/12">·</span>
          <a
            href="https://github.com/snowdamiz/cadence/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-[13px] text-white/40 hover:text-white/70 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            Report an issue
          </a>
        </div>
      </div>
    </section>
  )
}
