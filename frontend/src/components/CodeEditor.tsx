/**
 * CodeEditor – Monaco-based Python editor panel.
 * Exposes current code to parent via `onCodeChange`.
 * The "AI Optimize" button triggers the `onAIOptimize` callback
 * and shows the returned refactored code in the editor.
 */
import { useRef, useState } from 'react'
import MonacoEditor, { type OnMount } from '@monaco-editor/react'
import type * as monaco from 'monaco-editor'
import { Wand2, Play, RotateCcw, Copy, Check, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { AuditResponse } from '@/api/types'
import { cn } from '@/lib/utils'

const DEMO_CODE = `import numpy as np

# Inefficient loop-based distance computation (try AI Optimize!)
def pairwise_distances(X: np.ndarray) -> np.ndarray:
    n = X.shape[0]
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = X[i] - X[j]
            D[i, j] = np.sqrt((diff ** 2).sum())
    return D

# Generate a small point cloud for TDA
rng = np.random.default_rng(42)
points = rng.standard_normal((64, 3))
print("Point cloud shape:", points.shape)
`

export interface CodeEditorProps {
  onCodeChange?: (code: string) => void
  onAIOptimize?: (code: string) => Promise<AuditResponse | null>
  onRunCode?: (code: string) => void
  aiLoading?: boolean
}

export function CodeEditor({
  onCodeChange,
  onAIOptimize,
  onRunCode,
  aiLoading = false,
}: CodeEditorProps) {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null)
  const [code, setCode] = useState(DEMO_CODE)
  const [copied, setCopied] = useState(false)
  const [lastSuggestions, setLastSuggestions] = useState<AuditResponse | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)

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
    const result = await onAIOptimize(code)
    if (result) {
      setLastSuggestions(result)
      setShowSuggestions(true)
      if (result.refactored_code) {
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
    setCode(DEMO_CODE)
    editorRef.current?.setValue(DEMO_CODE)
    setLastSuggestions(null)
    setShowSuggestions(false)
  }

  const severityColor: Record<string, string> = {
    error: 'text-red-400',
    warn: 'text-amber-400',
    info: 'text-blue-400',
  }

  return (
    <div className="flex h-full flex-col bg-card border-r border-border">
      {/* Panel header */}
      <div className="flex items-center justify-between border-b border-border px-3 py-2 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-foreground tracking-wide uppercase">
            Code Editor
          </span>
          <Badge variant="muted" className="text-[10px]">
            Python
          </Badge>
        </div>
        <div className="flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={handleCopy}
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
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
            <TooltipContent>重置示例</TooltipContent>
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
        <Button
          variant="default"
          size="sm"
          onClick={handleAIOptimize}
          disabled={aiLoading || !onAIOptimize}
          className="bg-violet-600 hover:bg-violet-500 text-white gap-1.5"
        >
          {aiLoading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Wand2 className="h-3.5 w-3.5" />
          )}
          AI 优化
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => onRunCode?.(code)}
          disabled={!onRunCode}
          className="gap-1.5"
        >
          <Play className="h-3.5 w-3.5" />
          运行
        </Button>

        {lastSuggestions && (
          <button
            className="ml-auto text-xs text-muted-foreground underline-offset-2 hover:underline"
            onClick={() => setShowSuggestions((v) => !v)}
          >
            {showSuggestions ? '隐藏' : '查看'}建议 ({lastSuggestions.suggestions.length})
          </button>
        )}
      </div>

      {/* AI suggestions panel */}
      {showSuggestions && lastSuggestions && (
        <div className="border-t border-border bg-muted/30 max-h-40 overflow-y-auto shrink-0">
          <div className="px-3 pt-2 pb-1">
            <p className="text-xs text-muted-foreground">{lastSuggestions.summary}</p>
          </div>
          {lastSuggestions.suggestions.map((s, i) => (
            <div key={i} className="flex gap-2 px-3 py-1 border-t border-border/50">
              <span className={cn('text-xs shrink-0 font-medium', severityColor[s.severity])}>
                {s.severity.toUpperCase()}
              </span>
              <span className="text-xs text-muted-foreground">{s.rationale}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
