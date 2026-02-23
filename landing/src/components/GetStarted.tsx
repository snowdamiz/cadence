import { useScrollReveal } from '@/hooks/useScrollReveal'
import { useCopyToClipboard } from '@/hooks/useCopyToClipboard'
import { INSTALL_COMMANDS, REPO_URL, NPM_URL } from '@/lib/constants'
import { Copy, Check, Github, ExternalLink } from 'lucide-react'
import { Button } from './ui/button'

export function GetStarted() {
  const ref = useScrollReveal()
  const { copiedText, copy } = useCopyToClipboard()

  return (
    <section ref={ref} id="get-started" className="relative px-6 py-32">
      <div className="glow-periwinkle left-1/2 top-1/2 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2" />

      <div className="relative mx-auto max-w-3xl text-center">
        <div className="scroll-reveal mb-12">
          <p className="mb-3 text-sm font-medium uppercase tracking-widest text-salmon">
            Get started
          </p>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Ready to{' '}
            <span className="gradient-text-mixed">install</span>
          </h2>
        </div>

        <div className="scroll-reveal stagger-1 mb-10 space-y-3">
          {INSTALL_COMMANDS.map((cmd) => (
            <button
              key={cmd.label}
              onClick={() => copy(cmd.command)}
              className="glass-card-hover group flex w-full items-center gap-4 px-6 py-4 text-left"
            >
              <span className="shrink-0 rounded-lg bg-white/5 px-2 py-1 font-mono text-xs text-white/40">
                {cmd.label}
              </span>
              <code className="flex-1 truncate font-mono text-sm text-white/70">
                {cmd.command}
              </code>
              <span className="shrink-0 text-white/30 transition-colors group-hover:text-white/60">
                {copiedText === cmd.command ? (
                  <Check size={16} className="text-salmon" />
                ) : (
                  <Copy size={16} />
                )}
              </span>
            </button>
          ))}
        </div>

        <div className="scroll-reveal stagger-2 flex flex-wrap items-center justify-center gap-3">
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
            <Button variant="secondary" size="lg">
              <Github size={18} />
              GitHub
            </Button>
          </a>
          <a href={NPM_URL} target="_blank" rel="noopener noreferrer">
            <Button variant="ghost" size="lg">
              <ExternalLink size={18} />
              npm
            </Button>
          </a>
        </div>
      </div>
    </section>
  )
}
