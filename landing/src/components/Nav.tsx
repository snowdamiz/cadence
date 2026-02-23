import { useEffect, useState } from 'react'
import { Github } from 'lucide-react'

export function Nav() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 32)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-[#07070E]/85 backdrop-blur-xl border-b border-white/[0.06]'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="relative w-2 h-2">
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-salmon to-periwinkle" />
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-salmon to-periwinkle blur-[3px] opacity-70" />
            </div>
            <span className="font-mono font-bold text-[13px] tracking-[0.2em] text-white/80">
              CADENCE
            </span>
          </div>

          {/* Right nav */}
          <div className="flex items-center gap-1">
            <a
              href="https://www.npmjs.com/package/cadence-skill-installer"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 text-xs font-mono text-white/35 hover:text-white/65 transition-colors"
            >
              npm
            </a>
            <a
              href="https://github.com/snowdamiz/cadence"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-white/35 hover:text-white/65 transition-colors"
            >
              <Github className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </nav>
  )
}
