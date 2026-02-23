import { useCopyToClipboard } from '@/hooks/useCopyToClipboard'
import { TERMINAL_LINES, BANNER_LINES } from '@/lib/constants'
import { Copy, Check, ChevronDown } from 'lucide-react'
import { Button } from './ui/button'

const COLORS = {
  white: 'rgba(255,255,255,0.85)',
  salmon: '#FFAFAF',
  periwinkle: '#AFD7FF',
}

/** Renders the same Unicode banner used by the installer with a 3-color split */
function Banner({ delay }: { delay: number }) {
  return (
    <div
      className="animate-terminal-line opacity-0 my-2"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="m-0 overflow-x-auto text-[10px] sm:text-[15px] leading-none whitespace-pre">
        {BANNER_LINES.map((line, i) => {
          const third = Math.ceil(line.length / 3)
          const first = line.slice(0, third)
          const second = line.slice(third, third * 2)
          const thirdPart = line.slice(third * 2)

          return (
            <span key={i}>
              <span style={{ color: COLORS.white }}>{first}</span>
              <span style={{ color: COLORS.salmon }}>{second}</span>
              <span style={{ color: COLORS.periwinkle }}>{thirdPart}</span>
              {i < BANNER_LINES.length - 1 ? '\n' : null}
            </span>
          )
        })}
      </div>
    </div>
  )
}

export function Hero() {
  const { copiedText, copy } = useCopyToClipboard()
  const installCmd = 'npx cadence-skill-installer'

  let lineIndex = 0

  return (
    <section className="relative flex min-h-[calc(100dvh)] sm:min-h-screen items-center justify-center overflow-hidden px-6 pt-16">
      {/* Ambient glows */}
      <div className="glow-salmon -left-32 -top-32 h-[500px] w-[500px]" />
      <div className="glow-periwinkle -right-32 top-1/4 h-[400px] w-[400px]" />

      <div className="relative z-10 mx-auto max-w-6xl w-full">
        <div className="grid items-center gap-8 lg:gap-12 lg:grid-cols-2">
          {/* Left: copy */}
          <div className="max-w-xl">
            <p className="mb-5 font-mono text-xs font-medium uppercase tracking-widest text-white/30">
              Cadence
            </p>
            <h1 className="mb-6 text-4xl font-black tracking-tight leading-[1.1] sm:text-5xl lg:text-[3.5rem]">
              One workflow.{' '}
              <span className="gradient-text-periwinkle">Eight AI tools.</span>{' '}
              <span className="gradient-text-salmon">Zero chaos.</span>
            </h1>
            <p className="mb-8 text-base leading-relaxed text-white/55 sm:text-lg">
              A deterministic workflow engine with persistent state, guarded phase transitions, and atomic git checkpoints — installed in seconds.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button
                size="lg"
                onClick={() => copy(installCmd)}
                className="group font-mono text-xs sm:text-sm"
              >
                {copiedText === installCmd ? (
                  <>
                    <Check size={16} />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy size={16} />
                    {installCmd}
                  </>
                )}
              </Button>
              <a href="#architecture">
                <Button variant="secondary" size="lg">
                  How it works
                </Button>
              </a>
            </div>

            {/* Stats */}
            <div className="mt-10 flex flex-wrap gap-8">
              {[
                { value: '8', label: 'AI tools' },
                { value: '3', label: 'workflow phases' },
                { value: '∞', label: 'atomic checkpoints' },
              ].map((stat) => (
                <div key={stat.label} className="flex flex-col gap-0.5">
                  <span className="gradient-text-mixed text-3xl font-black leading-none">{stat.value}</span>
                  <span className="text-xs text-white/35 uppercase tracking-wider">{stat.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: terminal mockup */}
          <div className="glass-card overflow-hidden p-0 terminal-glow">
            {/* Title bar */}
            <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-3">
              <span className="h-3 w-3 rounded-full bg-[#FF5F57]/70" />
              <span className="h-3 w-3 rounded-full bg-[#FEBC2E]/70" />
              <span className="h-3 w-3 rounded-full bg-[#28C840]/70" />
              <span className="ml-3 text-xs text-white/30 font-mono">terminal</span>
            </div>
            {/* Terminal body */}
            <div className="p-3 sm:p-5 font-mono text-xs sm:text-[13px] leading-relaxed">
              {TERMINAL_LINES.map((line, i) => {
                if (line.type === 'banner') {
                  const bannerDelay = 0.3 + lineIndex * 0.1
                  lineIndex += 1
                  return <Banner key={i} delay={bannerDelay} />
                }

                const delay = 0.3 + lineIndex * 0.1
                lineIndex++

                if (line.type === 'prompt') {
                  return (
                    <div
                      key={i}
                      className="animate-terminal-line opacity-0"
                      style={{ animationDelay: `${delay}s` }}
                    >
                      <span className="text-periwinkle">$</span>{' '}
                      <span className="text-white/80">{line.text}</span>
                    </div>
                  )
                }

                if (line.type === 'blank') {
                  return (
                    <div
                      key={i}
                      className="animate-terminal-line opacity-0 h-4"
                      style={{ animationDelay: `${delay}s` }}
                    />
                  )
                }

                if (line.type === 'check') {
                  return (
                    <div
                      key={i}
                      className="animate-terminal-line opacity-0"
                      style={{ animationDelay: `${delay}s` }}
                    >
                      <span className="text-salmon"> ✓</span>
                      <span className="text-white/50"> {line.text}</span>
                    </div>
                  )
                }

                if (line.type === 'done') {
                  return (
                    <div
                      key={i}
                      className="animate-terminal-line opacity-0"
                      style={{ animationDelay: `${delay}s` }}
                    >
                      <span className="text-periwinkle"> {line.text}</span>
                    </div>
                  )
                }

                return null
              })}
              {/* Blinking cursor */}
              <div
                className="animate-terminal-line opacity-0 mt-1"
                style={{ animationDelay: `${0.3 + lineIndex * 0.1}s` }}
              >
                <span className="text-periwinkle">$</span>{' '}
                <span
                  className="terminal-cursor inline-block h-[14px] w-[7px] translate-y-[2px] bg-white/70"
                  style={{ animation: 'terminal-cursor-blink 1.1s step-end infinite' }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="scroll-indicator absolute bottom-8 left-1/2 -translate-x-1/2 z-10" style={{ animation: 'scroll-bounce 2.4s ease-in-out infinite' }}>
        <ChevronDown size={20} className="text-white/30" />
      </div>

      {/* Grid pattern overlay */}
      <div className="grid-pattern pointer-events-none absolute inset-0 opacity-50" />
    </section>
  )
}
