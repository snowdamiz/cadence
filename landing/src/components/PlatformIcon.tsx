import type { ToolKey } from '@/lib/constants'

type IconProps = {
  toolKey: ToolKey
  className?: string
}

function Svg({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      aria-hidden="true"
      focusable="false"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {children}
    </svg>
  )
}

export function PlatformIcon({ toolKey, className }: IconProps) {
  switch (toolKey) {
    case 'codex':
      return (
        <Svg className={className}>
          <path d="M12 3.5 18.8 7.4v9.2L12 20.5 5.2 16.6V7.4Z" />
          <path d="M12 7.6v3.1m0 2.6v3.1m-3.4-6.1 2.2 1.3m2.4 1.4 2.2 1.3m-6.8 0 2.2-1.3m2.4-1.4 2.2-1.3" />
        </Svg>
      )

    case 'agents':
      return (
        <Svg className={className}>
          <circle cx="12" cy="12" r="2.2" fill="currentColor" fillOpacity="0.2" />
          <circle cx="6.8" cy="7.2" r="2" />
          <circle cx="17.2" cy="7.2" r="2" />
          <circle cx="12" cy="17.6" r="2" />
          <path d="M8.3 8.6 10.4 10.5m5.3-1.9-2.1 1.9m-1.6 3.7v1.5" />
        </Svg>
      )

    case 'claude':
      return (
        <Svg className={className}>
          <path d="M12 4 18.4 20h-2.8l-1.3-3.4H9.7L8.4 20H5.6L12 4Z" />
          <path d="M10.4 14h3.2" />
        </Svg>
      )

    case 'gemini':
      return (
        <Svg className={className}>
          <path
            d="M12 2.8 14.4 9.6 21.2 12 14.4 14.4 12 21.2 9.6 14.4 2.8 12 9.6 9.6Z"
            fill="currentColor"
            fillOpacity="0.2"
          />
          <path d="M12 2.8 14.4 9.6 21.2 12 14.4 14.4 12 21.2 9.6 14.4 2.8 12 9.6 9.6Z" />
          <path d="M18.8 4.6v2.2m-1.1-1.1h2.2" />
        </Svg>
      )

    case 'copilot':
      return (
        <Svg className={className}>
          <path d="M10 8.4a3.6 3.6 0 1 0-3.4 6.3c2.3 1.2 4.1-.3 5.4-2.2 1.4-2 3-4.4 5.5-3.3a3.6 3.6 0 1 1-3.4 6.3" />
          <path d="M14 15.6a3.6 3.6 0 1 0 3.4-6.3c-2.3-1.2-4.1.3-5.4 2.2-1.4 2-3 4.4-5.5 3.3a3.6 3.6 0 1 1 3.4-6.3" />
        </Svg>
      )

    case 'github-copilot':
      return (
        <Svg className={className}>
          <path d="M12 4.2v2" />
          <rect x="5.1" y="7" width="13.8" height="10.3" rx="4.8" />
          <circle cx="9.4" cy="12.1" r="1.2" fill="currentColor" stroke="none" />
          <circle cx="14.6" cy="12.1" r="1.2" fill="currentColor" stroke="none" />
          <path d="M7.9 17.3v2m8.2-2v2m-9.2-9L5 9m12.1 0L19 9" />
        </Svg>
      )

    case 'windsurf':
      return (
        <Svg className={className}>
          <path d="M3.5 9.1c2.3 0 2.3 3.1 4.5 3.1s2.3-3.1 4.5-3.1 2.3 3.1 4.5 3.1 2.3-3.1 4.5-3.1" />
          <path d="M3.5 14.9c2.3 0 2.3 3.1 4.5 3.1s2.3-3.1 4.5-3.1 2.3 3.1 4.5 3.1 2.3-3.1 4.5-3.1" opacity="0.7" />
        </Svg>
      )

    case 'opencode':
      return (
        <Svg className={className}>
          <path d="m8.3 7-4 5 4 5m7.4-10 4 5-4 5m-2.7-11-2.2 12" />
        </Svg>
      )

    default:
      return null
  }
}
