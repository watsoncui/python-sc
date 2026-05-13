/**
 * useAI – wraps the /ai/audit/vectorize endpoint.
 * Call `optimize(code)` to request an AI vectorization audit.
 * The hook tracks loading state, errors, and the last response.
 */
import { useCallback, useRef, useState } from 'react'
import type { AuditRequest, AuditResponse, ProviderMode } from '@/api/types'
import { ApiError, apiClient } from '@/api/client'

export interface UseAIOptions {
  provider?: ProviderMode
  target?: AuditRequest['target']
  courseWeek?: number | null
  localKeyAlias?: string | null
}

export interface UseAIReturn {
  loading: boolean
  error: string | null
  result: AuditResponse | null
  optimize: (code: string) => Promise<AuditResponse | null>
  cancel: () => void
  reset: () => void
}

export function useAI(opts: UseAIOptions = {}): UseAIReturn {
  const {
    provider = 'server',
    target = 'vectorize',
    courseWeek = null,
    localKeyAlias = null,
  } = opts

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AuditResponse | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setLoading(false)
  }, [])

  const reset = useCallback(() => {
    cancel()
    setError(null)
    setResult(null)
  }, [cancel])

  const optimize = useCallback(
    async (code: string): Promise<AuditResponse | null> => {
      abortRef.current?.abort()
      const ac = new AbortController()
      abortRef.current = ac

      setLoading(true)
      setError(null)

      try {
        const req: AuditRequest = {
          code,
          provider,
          target,
          course_week: courseWeek,
          local_key_alias: localKeyAlias,
        }
        const res = await apiClient.post<AuditResponse>('/ai/audit/vectorize', req, ac.signal)
        setResult(res)
        return res
      } catch (err) {
        if (!ac.signal.aborted) {
          const msg = err instanceof ApiError ? err.detail : String(err)
          setError(msg)
        }
        return null
      } finally {
        if (!ac.signal.aborted) setLoading(false)
      }
    },
    [provider, target, courseWeek, localKeyAlias],
  )

  return { loading, error, result, optimize, cancel, reset }
}
