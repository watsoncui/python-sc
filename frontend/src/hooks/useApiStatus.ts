/**
 * useApiStatus – polls /healthz and / every N ms to track:
 *   - connection state (connecting | online | offline)
 *   - provider mode (server | local)
 *   - round-trip latency in ms
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import type { HealthResponse, ProviderMode, RootResponse } from '@/api/types'
import { apiClient } from '@/api/client'

export type ConnectionState = 'connecting' | 'online' | 'offline'

export interface ApiStatus {
  connection: ConnectionState
  mode: ProviderMode
  latencyMs: number | null
  version: string
  lastChecked: Date | null
  refresh: () => void
}

const POLL_INTERVAL_MS = 15_000

export function useApiStatus(): ApiStatus {
  const [connection, setConnection] = useState<ConnectionState>('connecting')
  const [mode, setMode] = useState<ProviderMode>('server')
  const [latencyMs, setLatencyMs] = useState<number | null>(null)
  const [version, setVersion] = useState('—')
  const [lastChecked, setLastChecked] = useState<Date | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const check = useCallback(async () => {
    abortRef.current?.abort()
    const ac = new AbortController()
    abortRef.current = ac

    const t0 = performance.now()
    try {
      await apiClient.get<HealthResponse>('/healthz', ac.signal)
      const elapsed = Math.round(performance.now() - t0)
      const root = await apiClient.get<RootResponse>('/', ac.signal)
      setLatencyMs(elapsed)
      setMode(root.mode)
      setVersion(root.version)
      setConnection('online')
    } catch {
      if (!ac.signal.aborted) {
        setConnection('offline')
        setLatencyMs(null)
      }
    } finally {
      setLastChecked(new Date())
    }
  }, [])

  useEffect(() => {
    check()
    const timer = setInterval(check, POLL_INTERVAL_MS)
    return () => {
      clearInterval(timer)
      abortRef.current?.abort()
    }
  }, [check])

  return { connection, mode, latencyMs, version, lastChecked, refresh: check }
}
