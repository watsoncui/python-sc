/**
 * CodeEditor – Monaco-based Python editor panel.
 * - "AI 优化" button with target selector (vectorize / explain / debug)
 * - Color-coded AI audit suggestions by category and severity
 * - Token usage display after AI response
 * - Line range annotations for each suggestion
 */
import { useRef, useState } from 'react'
import MonacoEditor, { type OnMount } from '@monaco-editor/react'
import type * as monaco from 'monaco-editor'
import { Wand2, Play, RotateCcw, Copy, Check, Loader2, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { AuditResponse, AuditTarget, AuditCategory, AuditSeverity } from '@/api/types'
import { cn } from '@/lib/utils'

const DEMO_CODE = `import numpy as np

# 低效的逐对距离计算（可点击「AI 优化」看向量化改写！）
def pairwise_distances(X: np.ndarray) -> np.ndarray:
    n = X.shape[0]
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = X[i] - X[j]
            D[i, j] = np.sqrt((diff ** 2).sum())
    return D

# 生成点云（可用于 TDA 分析）
rng = np.random.default_rng(42)
points = rng.standard_normal((64, 3))
D = pairwise_distances(points)
print("点云形状:", points.shape, "  距离矩阵:", D.shape)
`

// ── AI audit display helpers ─────────────────────────────────────────────────

const SEVERITY_COLOR: Record<AuditSeverity, string> = {
  error: 'text-red-400',
  warn:  'text-amber-400',
  info:  'text-blue-400',
}

const SEVERITY_BG: Record<AuditSeverity, string> = {
  error: 'bg-red-900/30 border-red-700/40',
  warn:  'bg-amber-900/30 border-amber-700/40',
  info:  'bg-blue-900/30 border-blue-700/40',
}

const CATEGORY_LABEL: Record<AuditCategory, string> = {
  vectorization:       '向量化',
  memory_layout:       '内存布局',
  numerical_stability: '数值稳定',
  api_correctness:     'API 正确性',
  style:               '风格',
}

const CATEGORY_COLOR: Record<AuditCategory, string> = {
  vectorization:       'text-violet-300',
  memory_layout:       'text-orange-300',
  numerical_stability: 'text-rose-300',
  api_correctness:     'text-amber-300',
  style:               'text-slate-400',
}

const TARGET_OPTIONS: { value: AuditTarget; label: string; desc: string }[] = [
  { value: 'vectorize', label: '向量化',  desc: '转化为 NumPy 向量化代码' },
  { value: 'explain',   label: '解释',    desc: '逐行解释代码含义' },
  { value: 'debug',     label: '调试',    desc: '找出潜在错误与数值陷阱' },
]

export interface CodeEditorProps {
  onCodeChange?: (code: string) => void
  onAIOptimize?: (code: string, target: AuditTarget) => Promise<AuditResponse | null>
  onRunCode?: (code: string) => void
  aiLoading?: boolean
  initialCode?: string
}

export function CodeEditor({
  onCodeChange,
  onAIOptimize,
  onRunCode,
  aiLoading = false,
  initialCode,
}: CodeEditorProps) {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null)
  const [code, setCode] = useState(initialCode ?? DEMO_CODE)
  const [copied, setCopied] = useState(false)
  const [lastResult, setLastResult] = useState<AuditResponse | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [target, setTarget] = useState<AuditTarget>('vectorize')
  const [targetDropdownOpen, setTargetDropdownOpen] = useState(false)

  const prevInitialRef = useRef(initialCode)
  if (initialCode && initialCode !== prevInitialRef.current) {
    prevInitialRef.current = initialCode
    setCode(initialCode)
    editorRef.current?.setValue(initialCode)
    setLastResult(null)
    setShowSuggestions(false)
  }

  const handleMount: OnMount = (editor) => {
    editorRef.current = editor
    editor.focus()
  }

  const handleChange = (value: string | undefined) => {
    const v = value ?? ''
    setCode(v)
    onCodeChange?.(v)
  }

  const handleAIOptimize = async () => {
    if (!onAIOptimize) return
    const result = await onAIOptimize(code, target)
    if (result) {
      setLastResult(result)
      setShowSuggestions(true)
      if (result.refactored_code && target === 'vectorize') {
        setCode(result.refactored_code)
        editorRef.current?.setValue(result.refactored_code)
      }
    }
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleReset = () => {
    const resetTo = initialCode ?? DEMO_CODE
    setCode(resetTo)
    editorRef.current?.setValue(resetTo)
    setLastResult(null)
    setShowSuggestions(false)
  }

  const currentTargetLabel = TARGET_OPTIONS.find((o) => o.value === target)?.label ?? '向量化'

  return (
    <div className="flex h-full flex-col bg-card">
      {/* Panel header */}
      <div className="flex items-center justify-between border-b border-border px-3 py-2 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-foreground tracking-wide uppercase">
            Code Editor
          </span>
          <Badge variant="muted" className="text-[10px]">Python</Badge>
        </div>
        <div className="flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleCopy}>
                {copied
                  ? <Check className="h-3.5 w-3.5 text-emerald-400" />
                  : <Copy className="h-3.5 w-3.5" />}
              </Button>
            </TooltipTrigger>
            <TooltipContent>复制代码</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleReset}>
                <RotateCcw className="h-3.5 w-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>重置为本周示例</TooltipContent>
          </Tooltip>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 min-h-0">
        <MonacoEditor
          language="python"
          theme="vs-dark"
          value={code}
          onChange={handleChange}
          onMount={handleMount}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Cascadia Code', Consolas, monospace",
            fontLigatures: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbers: 'on',
            renderWhitespace: 'selection',
            bracketPairColorization: { enabled: true },
            padding: { top: 8, bottom: 8 },
            smoothScrolling: true,
            cursorBlinking: 'smooth',
            wordWrap: 'on',
            automaticLayout: true,
          }}
        />
      </div>

      {/* Action bar */}
      <div className="border-t border-border px-3 py-2 flex items-center gap-2 shrink-0">
        {/* AI optimize button with target selector */}
        <div className="flex items-stretch rounded-md overflow-hidden border border-violet-600/50">
          <Button
            variant="default"
            size="sm"
            onClick={handleAIOptimize}
            disabled={aiLoading || !onAIOptimize}
            className="bg-violet-600 hover:bg-violet-500 text-white gap-1.5 rounded-none border-0 h-8"
          >
            {aiLoading
              ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
              : <Wand2 className="h-3.5 w-3.5" />}
            AI {currentTargetLabel}
          </Button>
          {/* Target dropdown */}
          <div className="relative">
            <button
              onClick={() => setTargetDropdownOpen((v) => !v)}
              className="h-8 px-1.5 bg-violet-700 hover:bg-violet-600 text-white transition-colors border-l border-violet-500/50"
            >
              <ChevronDown className="h-3 w-3" />
            </button>
            {targetDropdownOpen && (
              <div className="absolute bottom-full right-0 mb-1 bg-popover border border-border rounded-md shadow-lg z-20 w-40">
                {TARGET_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => { setTarget(opt.value); setTargetDropdownOpen(false) }}
                    className={cn(
                      'w-full text-left px-3 py-2 text-[11px] hover:bg-muted transition-colors',
                      target === opt.value ? 'text-violet-300' : 'text-foreground',
                    )}
                  >
                    <span className="font-medium">{opt.label}</span>
                    <span className="block text-[10px] text-muted-foreground">{opt.desc}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => onRunCode?.(code)}
          disabled={!onRunCode}
          className="gap-1.5 h-8"
        >
          <Play className="h-3.5 w-3.5" />
          运行
        </Button>

        {lastResult && (
          <div className="ml-auto flex items-center gap-2">
            {/* Token usage */}
            {lastResult.usage && (
              <span className="text-[10px] text-muted-foreground font-mono">
                {lastResult.usage.total_tokens} tokens
              </span>
            )}
            <button
              className="text-[11px] text-muted-foreground underline-offset-2 hover:underline"
              onClick={() => setShowSuggestions((v) => !v)}
            >
              {showSuggestions ? '隐藏' : '查看'}建议 ({lastResult.suggestions.length})
            </button>
          </div>
        )}
      </div>

      {/* AI suggestions panel – enhanced with categories and severity */}
      {showSuggestions && lastResult && (
        <div className="border-t border-border bg-muted/20 max-h-48 overflow-y-auto shrink-0">
          {/* Summary */}
          <div className="px-3 pt-2 pb-1 flex items-start gap-2">
            <Wand2 className="h-3.5 w-3.5 text-violet-400 shrink-0 mt-0.5" />
            <p className="text-[11px] text-muted-foreground">{lastResult.summary}</p>
          </div>

          {/* Suggestions */}
          {lastResult.suggestions.map((s, i) => (
            <div
              key={i}
              className={cn(
                'mx-3 mb-2 border rounded-md px-2 py-1.5',
                SEVERITY_BG[s.severity],
              )}
            >
              <div className="flex items-center gap-2 mb-0.5">
                <span className={cn('text-[10px] font-bold uppercase', SEVERITY_COLOR[s.severity])}>
                  {s.severity}
                </span>
                <span className={cn('text-[10px] font-medium', CATEGORY_COLOR[s.category])}>
                  {CATEGORY_LABEL[s.category]}
                </span>
                {s.line_range && (
                  <span className="text-[9px] text-muted-foreground font-mono ml-auto">
                    L{s.line_range[0]}–{s.line_range[1]}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-muted-foreground leading-snug">{s.rationale}</p>
              {s.rewritten_snippet && (
                <pre className="mt-1 text-[10px] bg-black/20 rounded px-2 py-1 overflow-x-auto text-foreground">
                  {s.rewritten_snippet}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
