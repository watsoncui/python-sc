/**
 * useCompute – wraps the /compute/run endpoint (sandboxed Python execution).
 */
import { useCallback, useRef, useState } from 'react'
import type { ComputeRequest, ComputeResponse } from '@/api/types'
import { ApiError, apiClient } from '@/api/client'

export interface UseComputeReturn {
  loading: boolean
  error: string | null
  result: ComputeResponse | null
  run: (code: string, inputs?: Record<string, unknown>) => Promise<ComputeResponse | null>
  cancel: () => void
  reset: () => void
}

export function useCompute(): UseComputeReturn {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ComputeResponse | null>(null)
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

  const run = useCallback(
    async (
      code: string,
      inputs: Record<string, unknown> = {},
    ): Promise<ComputeResponse | null> => {
      abortRef.current?.abort()
      const ac = new AbortController()
      abortRef.current = ac

      setLoading(true)
      setError(null)

      try {
        const req: ComputeRequest = { code, inputs, timeout_sec: 10 }
        const res = await apiClient.post<ComputeResponse>('/compute/run', req, ac.signal)
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
    [],
  )

  return { loading, error, result, run, cancel, reset }
}
