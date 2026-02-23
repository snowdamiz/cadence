import { useState, useCallback } from 'react'

export function useCopyToClipboard(resetMs = 2000) {
  const [copiedText, setCopiedText] = useState<string | null>(null)

  const copy = useCallback(
    async (text: string) => {
      try {
        await navigator.clipboard.writeText(text)
        setCopiedText(text)
        setTimeout(() => setCopiedText(null), resetMs)
      } catch {
        setCopiedText(null)
      }
    },
    [resetMs],
  )

  return { copiedText, copy }
}
