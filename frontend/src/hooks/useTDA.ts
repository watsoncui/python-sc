/**
 * useTDA – wraps the /tda/pipeline endpoint.
 * Feed a 2-D point cloud or raw code to get persistence diagram data.
 */
import { useCallback, useRef, useState } from 'react'
import type { TDARequest, TDAResponse } from '@/api/types'
import { ApiError, apiClient } from '@/api/client'

export interface UseTDAOptions {
  pipeline?: TDARequest['pipeline']
  maxDimension?: number
  maxEdgeLength?: number
  nBins?: number
}

export interface UseTDAReturn {
  loading: boolean
  error: string | null
  result: TDAResponse | null
  runPipeline: (data: number[][], opts?: Partial<TDARequest>) => Promise<TDAResponse | null>
  cancel: () => void
  reset: () => void
}

export function useTDA(defaults: UseTDAOptions = {}): UseTDAReturn {
  const {
    pipeline = 'vietoris_rips',
    maxDimension = 2,
    maxEdgeLength = 1.0,
    nBins = 100,
  } = defaults

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<TDAResponse | null>(null)
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

  const runPipeline = useCallback(
    async (data: number[][], overrides: Partial<TDARequest> = {}): Promise<TDAResponse | null> => {
      abortRef.current?.abort()
      const ac = new AbortController()
      abortRef.current = ac

      setLoading(true)
      setError(null)

      try {
        const req: TDARequest = {
          data,
          pipeline,
          max_dimension: maxDimension,
          max_edge_length: maxEdgeLength,
          n_bins: nBins,
          ...overrides,
        }
        const res = await apiClient.post<TDAResponse>('/tda/pipeline', req, ac.signal)
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
    [pipeline, maxDimension, maxEdgeLength, nBins],
  )

  return { loading, error, result, runPipeline, cancel, reset }
}
