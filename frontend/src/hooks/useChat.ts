/**
 * useChat – wraps the /ai/chat endpoint.
 * Maintains conversation history locally; each call appends messages.
 * Follows the "先回答→后推导→再追问" teaching pattern (see AI_PROMPTS.md §6).
 */
import { useCallback, useRef, useState } from 'react'
import type { ChatMessage, ChatRequest, ChatResponse, ProviderMode } from '@/api/types'
import { ApiError, apiClient } from '@/api/client'

export interface UseChatOptions {
  provider?: ProviderMode
  courseWeek?: number | null
  contextTags?: string[]
}

export interface ChatTurn {
  id: string
  userMessage: string
  assistantMessage: string | null
  knowledgeHits: string[]
  loading: boolean
  error: string | null
  timestamp: Date
}

export interface UseChatReturn {
  turns: ChatTurn[]
  loading: boolean
  send: (text: string) => Promise<void>
  clear: () => void
  cancel: () => void
}

let turnIdCounter = 0

export function useChat(opts: UseChatOptions = {}): UseChatReturn {
  const { provider = 'server', courseWeek = null, contextTags = [] } = opts
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [loading, setLoading] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  // Maintain full message history for context
  const historyRef = useRef<ChatMessage[]>([])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setLoading(false)
    setTurns((prev) =>
      prev.map((t) => (t.loading ? { ...t, loading: false, error: '已取消' } : t)),
    )
  }, [])

  const clear = useCallback(() => {
    cancel()
    setTurns([])
    historyRef.current = []
  }, [cancel])

  const send = useCallback(
    async (text: string) => {
      abortRef.current?.abort()
      const ac = new AbortController()
      abortRef.current = ac

      const id = `turn-${++turnIdCounter}`
      const userMsg: ChatMessage = { role: 'user', content: text }
      historyRef.current = [...historyRef.current, userMsg]

      const newTurn: ChatTurn = {
        id,
        userMessage: text,
        assistantMessage: null,
        knowledgeHits: [],
        loading: true,
        error: null,
        timestamp: new Date(),
      }

      setTurns((prev) => [...prev, newTurn])
      setLoading(true)

      try {
        const req: ChatRequest = {
          messages: historyRef.current,
          provider,
          temperature: 0.3,
          max_tokens: 1024,
          context_tags: [
            ...(courseWeek != null ? [`week${courseWeek}`] : []),
            ...contextTags,
          ],
        }
        const res = await apiClient.post<ChatResponse>('/ai/chat', req, ac.signal)

        historyRef.current = [...historyRef.current, res.reply]

        setTurns((prev) =>
          prev.map((t) =>
            t.id === id
              ? {
                  ...t,
                  assistantMessage: res.reply.content,
                  knowledgeHits: res.knowledge_hits,
                  loading: false,
                }
              : t,
          ),
        )
      } catch (err) {
        if (!ac.signal.aborted) {
          const msg = err instanceof ApiError ? err.detail : String(err)
          // Remove last user message from history on error
          historyRef.current = historyRef.current.slice(0, -1)
          setTurns((prev) =>
            prev.map((t) => (t.id === id ? { ...t, loading: false, error: msg } : t)),
          )
        }
      } finally {
        if (!ac.signal.aborted) setLoading(false)
      }
    },
    [provider, courseWeek, contextTags],
  )

  return { turns, loading, send, clear, cancel }
}
