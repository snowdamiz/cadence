import { useState, useCallback, useEffect, useRef } from 'react'

export function useCopyToClipboard(resetMs = 2000) {
  const [copiedText, setCopiedText] = useState<string | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const copy = useCallback(
    async (text: string) => {
      try {
        await navigator.clipboard.writeText(text)
        setCopiedText(text)
        if (timeoutRef.current !== null) {
          clearTimeout(timeoutRef.current)
        }
        timeoutRef.current = setTimeout(() => {
          setCopiedText(null)
          timeoutRef.current = null
        }, resetMs)
      } catch {
        setCopiedText(null)
      }
    },
    [resetMs],
  )

  useEffect(() => {
    return () => {
      if (timeoutRef.current !== null) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return { copiedText, copy }
}
