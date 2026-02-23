import { useEffect, useState } from 'react'
import { Badge } from './ui/badge'
import { VERSION, REPO_URL } from '@/lib/constants'
import { Github } from 'lucide-react'

export function Nav() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 32)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <nav
      className={`fixed top-0 z-50 w-full transition-all duration-300 ${
        scrolled
          ? 'border-b border-white/[0.06] bg-bg-base/80 backdrop-blur-lg'
          : 'bg-transparent'
      }`}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold tracking-tight">cadence</span>
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
