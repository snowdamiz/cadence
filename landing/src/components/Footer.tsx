import { REPO_URL, VERSION } from '@/lib/constants'
import { ArrowUp } from 'lucide-react'

export function Footer() {
  return (
    <footer className="border-t border-white/[0.06] px-6 py-6 sm:py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
        <span className="text-sm text-white/30">
          cadence v{VERSION}
        </span>
        <div className="flex items-center gap-6 text-sm text-white/30">
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-white/60"
          >
            GitHub
          </a>
          <a
            href="https://www.npmjs.com/package/cadence-skill-installer"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-white/60"
          >
            npm
          </a>
          <a
            href="#"
            className="flex items-center gap-1.5 transition-colors hover:text-white/60"
          >
            <ArrowUp size={14} />
            Top
          </a>
        </div>
      </div>
    </footer>
  )
}
