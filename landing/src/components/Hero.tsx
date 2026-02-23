import { useCopyToClipboard } from '@/hooks/useCopyToClipboard'
import { TERMINAL_LINES } from '@/lib/constants'
import { Copy, Check } from 'lucide-react'
import { Button } from './ui/button'

export function Hero() {
  const { copiedText, copy } = useCopyToClipboard()
  const installCmd = 'npx cadence-skill-installer'

  return (
    <section className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 pt-16">
      {/* Ambient glows */}
      <div className="glow-salmon -left-32 -top-32 h-[500px] w-[500px]" />
      <div className="glow-periwinkle -right-32 top-1/4 h-[400px] w-[400px]" />

      <div className="relative z-10 mx-auto max-w-6xl">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          {/* Left: copy */}
          <div className="max-w-xl">
            <h1 className="mb-6 text-6xl font-black tracking-tight sm:text-7xl lg:text-8xl">
              <span className="gradient-text-mixed">CADENCE</span>
            </h1>
            <p className="mb-8 text-lg leading-relaxed text-white/60 sm:text-xl">
              A deterministic workflow engine for AI tools.{' '}
              <span className="text-white/80">
                State machine, guarded routing, atomic checkpoints
              </span>{' '}
              — installed in seconds.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button
                size="lg"
                onClick={() => copy(installCmd)}
                className="group font-mono text-sm"
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
          </div>

          {/* Right: terminal mockup */}
          <div className="glass-card overflow-hidden p-0">
            {/* Title bar */}
            <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-3">
              <span className="h-3 w-3 rounded-full bg-white/10" />
              <span className="h-3 w-3 rounded-full bg-white/10" />
              <span className="h-3 w-3 rounded-full bg-white/10" />
              <span className="ml-3 text-xs text-white/30 font-mono">terminal</span>
            </div>
            {/* Terminal lines */}
            <div className="p-5 font-mono text-[13px] leading-relaxed">
              {TERMINAL_LINES.map((line, i) => (
                <div
                  key={i}
                  className="animate-terminal-line opacity-0"
                  style={{ animationDelay: `${0.3 + i * 0.15}s` }}
                >
                  {line.prompt ? (
                    <span>
                      <span className="text-periwinkle">$</span>{' '}
                      <span className="text-white/80">{line.text}</span>
                    </span>
                  ) : line.text === '' ? (
                    <br />
                  ) : line.text.startsWith(' ✓') ? (
                    <span>
                      <span className="text-salmon"> ✓</span>
                      <span className="text-white/50">{line.text.slice(2)}</span>
                    </span>
                  ) : line.text.includes('Done') ? (
                    <span className="text-periwinkle">{line.text}</span>
                  ) : line.text.includes('█') || line.text.includes('╗') || line.text.includes('║') || line.text.includes('╝') || line.text.includes('╚') || line.text.includes('═') ? (
                    <span className="text-salmon/70">{line.text}</span>
                  ) : (
                    <span className="text-white/40">{line.text}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Grid pattern overlay */}
      <div className="grid-pattern pointer-events-none absolute inset-0 opacity-50" />
    </section>
  )
}
