/**
 * TypeScript types mirroring the FastAPI Pydantic models.
 * Source: scicompute_assistant/common/protocols/
 */

// ─── Provider Mode ──────────────────────────────────────────────────────────

export type ProviderMode = 'server' | 'local'

// ─── Chat ────────────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
}

export interface LLMUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  model: string
  provider: ProviderMode
}

export interface ChatRequest {
  messages: ChatMessage[]
  provider?: ProviderMode
  temperature?: number
  max_tokens?: number
  model?: string | null
  local_key_alias?: string | null
  context_tags?: string[]
}

export interface ChatResponse {
  reply: ChatMessage
  usage: LLMUsage
  knowledge_hits: string[]
}

// ─── Code Audit ──────────────────────────────────────────────────────────────

export type AuditTarget = 'vectorize' | 'explain' | 'debug'
export type AuditSeverity = 'info' | 'warn' | 'error'
export type AuditCategory =
  | 'vectorization'
  | 'memory_layout'
  | 'numerical_stability'
  | 'api_correctness'
  | 'style'

export interface AuditRequest {
  code: string
  provider?: ProviderMode
  local_key_alias?: string | null
  course_week?: number | null
  target?: AuditTarget
}

export interface AuditSuggestion {
  category: AuditCategory
  severity: AuditSeverity
  line_range: [number, number] | null
  rationale: string
  rewritten_snippet: string | null
}

export interface AuditResponse {
  summary: string
  suggestions: AuditSuggestion[]
  refactored_code: string | null
  usage: LLMUsage
}

// ─── Compute (sandboxed execution) ───────────────────────────────────────────

export interface ComputeRequest {
  code: string
  inputs?: Record<string, unknown>
  timeout_sec?: number
  capture_stdout?: boolean
}

export interface ComputeResponse {
  ok: boolean
  stdout: string
  stderr: string
  result: Record<string, unknown>
  elapsed_ms: number
  error: string | null
}

// ─── TDA ─────────────────────────────────────────────────────────────────────

export type TDAPipeline = 'vietoris_rips' | 'alpha' | 'cubical' | 'mapper'

export interface TDARequest {
  data?: number[][] | null
  code?: string | null
  pipeline?: TDAPipeline
  max_dimension?: number
  max_edge_length?: number
  n_bins?: number
  downsample_preview?: number
}

export interface PersistencePoint {
  birth: number
  death: number
  dimension: number
  persistence: number
}

export interface BettiCurve {
  dimension: number
  filtration: number[]
  values: number[]
}

export interface PersistenceDiagramPayload {
  points: PersistencePoint[]
  max_filtration: number
  axis_limits: [number, number]
  betti_curves: BettiCurve[]
  point_cloud_preview: number[][] | null
  scale: 'linear' | 'log'
}

export interface TDAResponse {
  diagram: PersistenceDiagramPayload
  elapsed_ms: number
  backend: string
  warnings: string[]
}

// ─── Health / Status ─────────────────────────────────────────────────────────

export interface HealthResponse {
  status: 'ok' | 'error'
}

export interface RootResponse {
  name: string
  mode: ProviderMode
  version: string
}
