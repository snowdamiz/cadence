import { Github } from 'lucide-react'

export function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className="relative border-t border-white/[0.06] py-10 px-5">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-5">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="relative w-1.5 h-1.5">
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-salmon to-periwinkle" />
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-salmon to-periwinkle blur-[2px] opacity-70" />
          </div>
          <span className="font-mono text-[11px] font-bold tracking-[0.22em] text-white/35">
            CADENCE
          </span>
        </div>

        {/* Links */}
        <div className="flex items-center gap-5">
          <a
            href="https://github.com/snowdamiz/cadence"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-[12px] text-white/28 hover:text-white/55 transition-colors"
          >
            <Github className="w-3.5 h-3.5" />
            GitHub
          </a>
          <a
            href="https://www.npmjs.com/package/cadence-skill-installer"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[12px] text-white/28 hover:text-white/55 transition-colors"
          >
            npm
          </a>
          <a
            href="https://github.com/snowdamiz/cadence/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[12px] text-white/28 hover:text-white/55 transition-colors"
          >
            Issues
          </a>
        </div>

        {/* Copyright */}
        <p className="text-[11px] text-white/18 font-mono">
          &copy; {year} cadence-skill-installer
        </p>
      </div>
    </footer>
  )
}
