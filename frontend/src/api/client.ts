/**
 * Thin fetch wrapper for the FastAPI backend.
 * All requests go through /api/* (proxied by Vite dev server to localhost:8000).
 */

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(`API ${status}: ${detail}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
    signal,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const json = await res.json()
      detail = json.detail ?? detail
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export const apiClient = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>('GET', path, undefined, signal),
  post: <T>(path: string, body: unknown, signal?: AbortSignal) =>
    request<T>('POST', path, body, signal),
}
