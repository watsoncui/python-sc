/**
 * App – three-column layout:
 *   Left   : Monaco Editor + AI Optimize controls
 *   Right  : Plotly visualization (upper) + TDA Inspector (lower)
 *   Bottom : Status bar
 *
 * Hook wiring:
 *   useApiStatus  → status bar
 *   useAI         → editor AI optimize button
 *   useTDA        → TDA inspector + persistence plot
 *   useCompute    → run button (stdout display)
 */
import { useCallback, useRef, useState } from 'react'
import type { Data, Layout } from 'plotly.js'
import { TooltipProvider } from '@/components/ui/tooltip'
import { CodeEditor } from '@/components/CodeEditor'
import { PlotlyViewer } from '@/components/PlotlyViewer'
import { TDAInspector } from '@/components/TDAInspector'
import { StatusBar } from '@/components/StatusBar'
import { useApiStatus } from '@/hooks/useApiStatus'
import { useAI } from '@/hooks/useAI'
import { useTDA } from '@/hooks/useTDA'
import { useCompute } from '@/hooks/useCompute'
import type { TDAResponse } from '@/api/types'
import { cn } from '@/lib/utils'

/** Build Plotly traces from a TDA response (persistence diagram). */
function tdaToPlotData(res: TDAResponse): { data: Data[]; layout: Partial<Layout> } {
  const byDim = new Map<number, { x: number[]; y: number[] }>()
  const dimColors: Record<number, string> = {
    0: '#34d399',
    1: '#a78bfa',
    2: '#fbbf24',
    3: '#f87171',
  }
  const dimNames: Record<number, string> = { 0: 'H₀', 1: 'H₁', 2: 'H₂', 3: 'H₃' }

  for (const pt of res.diagram.points) {
    if (!byDim.has(pt.dimension)) byDim.set(pt.dimension, { x: [], y: [] })
    const bucket = byDim.get(pt.dimension)!
    bucket.x.push(pt.birth)
    bucket.y.push(pt.death === Infinity || pt.death > 1e6 ? res.diagram.max_filtration : pt.death)
  }

  const data: Data[] = []
  byDim.forEach((pts, dim) => {
    data.push({
      type: 'scatter',
      mode: 'markers',
      name: dimNames[dim] ?? `H${dim}`,
      x: pts.x,
      y: pts.y,
      marker: {
        color: dimColors[dim] ?? '#9ca3af',
        size: 6,
        opacity: 0.8,
      },
    } as Data)
  })

  // Diagonal
  const max = res.diagram.axis_limits[1]
  data.push({
    type: 'scatter',
    mode: 'lines',
    x: [0, max],
    y: [0, max],
    name: 'diagonal',
    line: { color: '#4b5563', dash: 'dash', width: 1 },
    showlegend: false,
  } as Data)

  const baseLayout: Partial<Layout> = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#9ca3af', size: 11 },
    margin: { l: 50, r: 20, t: 40, b: 50 },
    xaxis: {
      title: { text: 'Birth' },
      gridcolor: '#2e303a',
      zerolinecolor: '#4b5563',
    },
    yaxis: {
      title: { text: 'Death' },
      gridcolor: '#2e303a',
      zerolinecolor: '#4b5563',
    },
    title: { text: '持久性图谱', font: { size: 12 } },
    legend: { font: { size: 10 } },
    autosize: true,
  }

  return { data, layout: baseLayout }
}

/** Resizable divider between two panels. */
function VSplitter({ onDrag }: { onDrag: (dy: number) => void }) {
  const dragging = useRef(false)
  const lastY = useRef(0)

  return (
    <div
      className="h-1.5 cursor-row-resize bg-border/50 hover:bg-violet-600/40 transition-colors shrink-0 select-none"
      onMouseDown={(e) => {
        dragging.current = true
        lastY.current = e.clientY
        const onMove = (ev: MouseEvent) => {
          if (!dragging.current) return
          onDrag(ev.clientY - lastY.current)
          lastY.current = ev.clientY
        }
        const onUp = () => {
          dragging.current = false
          window.removeEventListener('mousemove', onMove)
          window.removeEventListener('mouseup', onUp)
        }
        window.addEventListener('mousemove', onMove)
        window.addEventListener('mouseup', onUp)
      }}
    />
  )
}

export default function App() {
  const apiStatus = useApiStatus()
  const ai = useAI()
  const tda = useTDA({ maxDimension: 2 })
  const compute = useCompute()

  // Current code in the editor (used by run/TDA callbacks)
  const codeRef = useRef('')
  const setCode = (c: string) => { codeRef.current = c }
  // TDA visualisation data
  const [plotOverride, setPlotOverride] = useState<{
    data: Data[]
    layout: Partial<Layout>
    title: string
  } | null>(null)
  // Resizable right column split (px from top)
  const [rightSplit, setRightSplit] = useState(0.55) // fraction of right-panel height

  const handleTDArun = useCallback(async () => {
    // Use a small demo point cloud when the editor has no parseable output yet
    const demoCloud = Array.from({ length: 120 }, () => {
      const theta = Math.random() * 2 * Math.PI
      const r = 1 + (Math.random() - 0.5) * 0.2
      return [r * Math.cos(theta), r * Math.sin(theta), (Math.random() - 0.5) * 0.4]
    })

    const res = await tda.runPipeline(demoCloud, { downsample_preview: 120 })
    if (!res) return

    // Prefer persistence diagram view after TDA run
    const diagramPlot = tdaToPlotData(res)
    setPlotOverride({ ...diagramPlot, title: '持久性图谱' })
  }, [tda])

  const handleRunCode = useCallback(
    async (src: string) => {
      await compute.run(src)
      // If compute yields a point cloud via result.points, pipe to TDA automatically
    },
    [compute],
  )

  const handleDrag = useCallback((dy: number) => {
    setRightSplit((prev) => {
      const next = prev + dy / window.innerHeight
      return Math.min(0.85, Math.max(0.15, next))
    })
  }, [])

  return (
    <TooltipProvider delayDuration={300}>
      <div className="flex flex-col h-screen bg-background overflow-hidden">
        {/* Title bar */}
        <div className="flex items-center gap-3 px-4 py-2 border-b border-border bg-card shrink-0">
          <div className="flex gap-1.5">
            <span className="h-3 w-3 rounded-full bg-red-500/70" />
            <span className="h-3 w-3 rounded-full bg-amber-500/70" />
            <span className="h-3 w-3 rounded-full bg-emerald-500/70" />
          </div>
          <span className="text-sm font-semibold text-foreground">
            SciCompute Assistant
          </span>
          <span className="text-xs text-muted-foreground ml-1">
            Scientific Python · TDA · AI Optimization
          </span>
        </div>

        {/* Main three-column area */}
        <div className="flex flex-1 min-h-0">
          {/* ── Left: Code Editor ────────────────────────────── */}
          <div className="w-[45%] min-w-[300px] flex flex-col overflow-hidden border-r border-border">
            <CodeEditor
              onCodeChange={setCode}
              onAIOptimize={ai.optimize}
              onRunCode={handleRunCode}
              aiLoading={ai.loading}
            />
          </div>

          {/* ── Right column: Plotly + TDA ───────────────────── */}
          <div className="flex-1 flex flex-col min-h-0 min-w-0">
            {/* Plotly upper panel */}
            <div
              className="overflow-hidden"
              style={{ height: `calc(${rightSplit * 100}% - 3px)` }}
            >
              <PlotlyViewer
                data={plotOverride?.data}
                layout={plotOverride?.layout}
                title={plotOverride?.title ?? 'Visualization'}
                isLoading={tda.loading}
                className="h-full"
              />
            </div>

            <VSplitter onDrag={handleDrag} />

            {/* TDA Inspector lower panel */}
            <div
              className="overflow-hidden"
              style={{ height: `calc(${(1 - rightSplit) * 100}% - 3px)` }}
            >
              <TDAInspector
                result={tda.result}
                loading={tda.loading}
                error={tda.error}
                onRun={handleTDArun}
                className="h-full"
              />
            </div>
          </div>
        </div>

        {/* ── Stdout / compute output strip ───────────────────── */}
        {(compute.result || compute.loading || compute.error) && (
          <div
            className={cn(
              'border-t border-border bg-muted/20 px-4 py-2 max-h-28 overflow-y-auto shrink-0',
            )}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-muted-foreground uppercase font-semibold tracking-wide">
                输出
              </span>
              <button
                className="text-[10px] text-muted-foreground hover:text-foreground"
                onClick={compute.reset}
              >
                清除
              </button>
            </div>
            {compute.loading && (
              <span className="text-[11px] text-sky-400 animate-pulse">运行中…</span>
            )}
            {compute.error && (
              <pre className="text-[11px] text-red-400 whitespace-pre-wrap">{compute.error}</pre>
            )}
            {compute.result && (
              <>
                {compute.result.stdout && (
                  <pre className="text-[11px] text-foreground whitespace-pre-wrap">
                    {compute.result.stdout}
                  </pre>
                )}
                {compute.result.stderr && (
                  <pre className="text-[11px] text-amber-400 whitespace-pre-wrap">
                    {compute.result.stderr}
                  </pre>
                )}
                {!compute.result.ok && compute.result.error && (
                  <pre className="text-[11px] text-red-400 whitespace-pre-wrap">
                    {compute.result.error}
                  </pre>
                )}
              </>
            )}
          </div>
        )}

        {/* ── Status bar ─────────────────────────────────────── */}
        <StatusBar
          status={apiStatus}
          aiLoading={ai.loading}
          tdaLoading={tda.loading}
          computeLoading={compute.loading}
        />
      </div>
    </TooltipProvider>
  )
}
