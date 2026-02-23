import { useEffect, useState } from 'react'
import { Badge } from './ui/badge'
import { VERSION, REPO_URL } from '@/lib/constants'
import { Github } from 'lucide-react'

function CadenceLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="cadence-logo-grad" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFAFAF" />
          <stop offset="100%" stopColor="#AFD7FF" />
        </linearGradient>
      </defs>
      <rect x="2.5" y="7" width="5" height="10" rx="2.5" fill="url(#cadence-logo-grad)" />
      <rect x="9.5" y="4" width="5" height="16" rx="2.5" fill="url(#cadence-logo-grad)" />
      <rect x="16.5" y="6" width="5" height="12" rx="2.5" fill="url(#cadence-logo-grad)" />
    </svg>
  )
}

export function Nav() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 32)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <nav
      className={`fixed top-0 z-50 w-full border-b transition-all duration-300 ${
        scrolled
          ? 'border-white/[0.06] bg-bg-base/80 backdrop-blur-lg'
          : 'border-transparent bg-transparent'
      }`}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <a href="#" aria-label="Cadence home" className="group relative flex items-center gap-2 text-lg font-bold tracking-tight">
            <CadenceLogo className="h-5 w-5 shrink-0" />
            <span className="transition-opacity duration-300 group-hover:opacity-0">cadence</span>
            <span className="gradient-text-mixed absolute left-7 right-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" aria-hidden="true">cadence</span>
          </a>
          <Badge variant="periwinkle">v{VERSION}</Badge>
        </div>

        <div className="flex items-center gap-4">
          <a
            href="#get-started"
            className="hidden text-sm text-white/50 transition-colors hover:text-white sm:block"
          >
            Install
          </a>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-sm text-white/70 transition-all hover:border-white/20 hover:text-white"
          >
            <Github size={16} />
            <span className="hidden sm:inline">GitHub</span>
          </a>
        </div>
      </div>
    </nav>
  )
}
