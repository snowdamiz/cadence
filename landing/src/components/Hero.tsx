import { useState } from 'react'
import { Copy, Check, ChevronDown } from 'lucide-react'

const COMMAND = 'npx cadence-skill-installer'

function TerminalWindow() {
  return (
    <div className="relative rounded-xl overflow-hidden border border-white/[0.07] bg-[#060610] shadow-2xl">
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/[0.05] bg-white/[0.015]">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-[#FF5F57]/55" />
          <div className="w-2.5 h-2.5 rounded-full bg-[#FEBC2E]/55" />
          <div className="w-2.5 h-2.5 rounded-full bg-[#28C840]/55" />
        </div>
        <span className="text-white/[0.35] text-[11px] font-mono mx-auto pr-10 tracking-wide">
          cadence-skill-installer
        </span>
      </div>

      {/* Terminal body */}
      <div className="p-5 font-mono text-[12px] leading-[1.7]">
        <div>
          <span className="text-periwinkle">❯</span>{' '}
          <span className="text-white/60">npx cadence-skill-installer</span>
        </div>

        <div className="mt-3 text-white/[0.18] text-[10px] tracking-widest">
          ── Cadence Skill Installer{' '}
          <span className="text-salmon/60">v0.2.7</span>{' '}
          ─────────────────────
        </div>

        <div className="mt-3">
          <span className="text-white/40">? </span>
          <span className="text-white/70">Select tools to install to</span>
        </div>
        <div className="text-white/25 text-[11px] mb-1">  (Space to toggle, Enter to confirm)</div>

        <div>
          <span className="text-periwinkle">  ❯ ◉ </span>
          <span className="text-white/80">Claude Code</span>
        </div>
        <div>
          <span className="text-white/35">    ◉ </span>
          <span className="text-white/55">Codex CLI</span>
        </div>
        <div>
          <span className="text-white/35">    ◉ </span>
          <span className="text-white/55">Gemini CLI</span>
        </div>
        <div>
          <span className="text-white/18">    ○ </span>
          <span className="text-white/30">GitHub Copilot</span>
        </div>
        <div>
          <span className="text-white/18">    ○ </span>
          <span className="text-white/30">Windsurf</span>
        </div>
        <div>
          <span className="text-white/18">    ○ </span>
          <span className="text-white/30">OpenCode</span>
        </div>

        <div className="mt-4 pt-4 border-t border-white/[0.04]">
          <div>
            <span className="text-green-400/75">✔ </span>
            <span className="text-white/55">Installed to </span>
            <span className="text-green-400/75">3 tools</span>
          </div>
          <div className="text-white/25 text-[11px] mt-0.5">
            &nbsp;&nbsp;→ claude, codex, gemini
          </div>
          <div className="text-white/20 text-[11px]">
            &nbsp;&nbsp;→ skills written to each tool's skill directory
          </div>
        </div>

        <div className="mt-4">
          <span className="text-periwinkle">❯</span>{' '}
          <span className="terminal-cursor" />
        </div>
      </div>
    </div>
  )
}

export function Hero() {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(COMMAND)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <section className="relative min-h-screen flex flex-col justify-center px-5 pt-24 pb-20 overflow-hidden">
      {/* Grid background */}
      <div className="absolute inset-0 grid-pattern opacity-50 pointer-events-none" />

      {/* Ambient glows */}
      <div
        className="absolute top-0 right-0 w-[800px] h-[600px] pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at top right, rgba(175, 215, 255, 0.12) 0%, transparent 60%)',
        }}
      />
      <div
        className="absolute bottom-0 left-0 w-[600px] h-[500px] pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at bottom left, rgba(255, 175, 175, 0.09) 0%, transparent 60%)',
        }}
      />

      <div className="relative z-10 max-w-6xl mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 xl:gap-20 items-center">
          {/* Left — text */}
          <div className="flex flex-col">
            {/* Version badge */}
            <div className="mb-8 inline-flex w-fit items-center gap-2 px-3 py-1.5 rounded-full border border-white/[0.14] bg-white/[0.04]">
              <span className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-salmon to-periwinkle" />
              <span className="font-mono text-[11px] text-white/55 tracking-widest">
                v0.2.7 &mdash; now on npm
              </span>
            </div>

            {/* Wordmark — gradient replaces broken block-char ASCII */}
            <div className="mb-5 select-none" aria-label="CADENCE">
              <span
                className="font-mono font-black tracking-tighter leading-[0.95] block wordmark-gradient"
                style={{ fontSize: 'clamp(54px, 9.5vw, 112px)' }}
              >
                CADENCE
              </span>
            </div>

            {/* Tagline */}
            <p className="text-lg sm:text-xl font-medium text-white/85 mb-3 leading-snug max-w-[420px]">
              Structured project operating system{' '}
              <span className="text-gradient">for AI-driven development</span>
            </p>

            {/* Description */}
            <p className="text-sm text-white/55 leading-relaxed mb-10 max-w-[380px]">
              Turn ad-hoc AI behavior into repeatable workflows — deterministic
              routing, persisted state, and rollback-safe git checkpoints across
              eight tools.
            </p>

            {/* Install command CTA */}
            <div className="flex flex-col gap-2.5">
              <button
                onClick={handleCopy}
                className="group flex items-center gap-3 px-5 py-3.5 code-block w-fit hover:border-white/[0.18] transition-all duration-200"
                title="Click to copy"
              >
                <span className="font-mono text-xs text-white/40">$</span>
                <code className="font-mono text-sm text-white/90">
                  {COMMAND}
                </code>
                <span className="ml-3 text-white/40 group-hover:text-white/65 transition-colors flex-shrink-0">
                  {copied ? (
                    <Check className="w-3.5 h-3.5 text-green-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </span>
              </button>
              <p className="text-[11px] text-white/38 font-mono pl-1">
                Requires Node &ge; 18
              </p>
            </div>
          </div>

          {/* Right — terminal window (desktop only) */}
          <div className="hidden lg:block">
            <TerminalWindow />
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 text-white/30">
        <ChevronDown className="w-4 h-4 animate-scroll-down" />
      </div>
    </section>
  )
}
