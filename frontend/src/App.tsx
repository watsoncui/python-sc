/**
 * App – three-column layout with teaching chat panel.
 *
 * Left   : WeekSelector + CodeEditor (+ AI target selector)
 * Center : Plotly visualization + TDA Inspector (resizable)
 * Right  : ChatPanel (teaching AI chat, /ai/chat)
 * Bottom : StatusBar (provider mode toggle + connection + latency)
 * Modal  : SyllabusInfo (course objectives / AI policy / assessment)
 */
import { useCallback, useRef, useState } from 'react'
import type { Data, Layout } from 'plotly.js'
import { TooltipProvider } from '@/components/ui/tooltip'
import { CodeEditor } from '@/components/CodeEditor'
import { PlotlyViewer } from '@/components/PlotlyViewer'
import { TDAInspector } from '@/components/TDAInspector'
import { StatusBar } from '@/components/StatusBar'
import { WeekSelector } from '@/components/WeekSelector'
import { ChatPanel } from '@/components/ChatPanel'
import { SyllabusInfo } from '@/components/SyllabusInfo'
import { useApiStatus } from '@/hooks/useApiStatus'
import { useAI } from '@/hooks/useAI'
import { useTDA } from '@/hooks/useTDA'
import { useCompute } from '@/hooks/useCompute'
import { useChat } from '@/hooks/useChat'
import WEEKS from '@/data/syllabusWeeks'
import type { TDAResponse, ProviderMode, AuditTarget } from '@/api/types'
import { cn } from '@/lib/utils'

/** Build Plotly traces from TDA persistence diagram. */
function tdaToPlotData(res: TDAResponse): { data: Data[]; layout: Partial<Layout> } {
  const byDim = new Map<number, { x: number[]; y: number[]; p: number[] }>()
  const dimColors: Record<number, string> = { 0: '#34d399', 1: '#a78bfa', 2: '#fbbf24', 3: '#f87171' }
  const dimNames: Record<number, string> = { 0: 'H₀', 1: 'H₁', 2: 'H₂', 3: 'H₃' }

  for (const pt of res.diagram.points) {
    if (!byDim.has(pt.dimension)) byDim.set(pt.dimension, { x: [], y: [], p: [] })
    const b = byDim.get(pt.dimension)!
    b.x.push(pt.birth)
    b.y.push(pt.death === Infinity || pt.death > 1e6 ? res.diagram.max_filtration : pt.death)
    b.p.push(pt.persistence)
  }

  const data: Data[] = []
  byDim.forEach((pts, dim) => {
    data.push({
      type: 'scattergl', mode: 'markers',
      name: dimNames[dim] ?? `H${dim}`,
      x: pts.x, y: pts.y,
      customdata: pts.p,
      hovertemplate: 'birth=%{x:.3f}<br>death=%{y:.3f}<br>persist=%{customdata:.3f}<extra></extra>',
      marker: { color: dimColors[dim] ?? '#9ca3af', size: 6, opacity: 0.85 },
    } as Data)
  })
  const max = res.diagram.axis_limits[1]
  data.push({
    type: 'scattergl', mode: 'lines',
    x: [0, max], y: [0, max],
    line: { color: '#4b5563', dash: 'dash', width: 1 },
    showlegend: false,
  } as Data)

  return {
    data,
    layout: {
      paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#9ca3af', size: 11 },
      margin: { l: 50, r: 20, t: 40, b: 50 },
      xaxis: { title: { text: 'Birth' }, gridcolor: '#2e303a', zerolinecolor: '#4b5563', scaleanchor: 'y' },
      yaxis: { title: { text: 'Death' }, gridcolor: '#2e303a', zerolinecolor: '#4b5563' },
      title: { text: '持久性图谱', font: { size: 12 } },
      legend: { font: { size: 10 } },
      autosize: true,
    },
  }
}

/** Resizable vertical splitter. */
function VSplitter({ onDrag }: { onDrag: (dy: number) => void }) {
  const dragging = useRef(false)
  const lastY = useRef(0)
  return (
    <div
      className="h-1.5 cursor-row-resize bg-border/50 hover:bg-violet-600/40 transition-colors shrink-0 select-none"
      onMouseDown={(e) => {
        dragging.current = true; lastY.current = e.clientY
        const onMove = (ev: MouseEvent) => { if (!dragging.current) return; onDrag(ev.clientY - lastY.current); lastY.current = ev.clientY }
        const onUp = () => { dragging.current = false; window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
        window.addEventListener('mousemove', onMove); window.addEventListener('mouseup', onUp)
      }}
    />
  )
}

export default function App() {
  // ── Week state ──
  const [selectedWeek, setSelectedWeek] = useState(1)
  const currentWeek = WEEKS.find((w) => w.week === selectedWeek) ?? WEEKS[0]
  // Current lesson AI prompt template (first lesson with hasAI:true)
  const aiLesson = currentWeek.lessons.find((l) => l.hasAI)

  // ── Provider mode ──
  const [provider, setProvider] = useState<ProviderMode>('server')
  const toggleProvider = useCallback(() => {
    setProvider((p) => (p === 'server' ? 'local' : 'server'))
  }, [])

  // ── Hooks ──
  const apiStatus = useApiStatus()
  const ai = useAI({ provider, target: 'vectorize', courseWeek: selectedWeek })
  const tda = useTDA({ maxDimension: 2 })
  const compute = useCompute()
  const chat = useChat({ provider, courseWeek: selectedWeek, contextTags: currentWeek.contextTags })

  // ── UI state ──
  const codeRef = useRef(currentWeek.demoCode)
  const [plotOverride, setPlotOverride] = useState<{ data: Data[]; layout: Partial<Layout>; title: string } | null>(null)
  const [rightSplit, setRightSplit] = useState(0.55)
  const [syllabusOpen, setSyllabusOpen] = useState(false)

  // ── Handlers ──
  const handleWeekChange = useCallback((week: number) => {
    setSelectedWeek(week)
    ai.reset(); compute.reset(); tda.reset(); setPlotOverride(null)
  }, [ai, compute, tda])

  const handleTDArun = useCallback(async () => {
    const cloud = Array.from({ length: 120 }, () => {
      const theta = Math.random() * 2 * Math.PI
      const r = 1 + (Math.random() - 0.5) * 0.2
      return [r * Math.cos(theta), r * Math.sin(theta), (Math.random() - 0.5) * 0.4]
    })
    const res = await tda.runPipeline(cloud, { downsample_preview: 120 })
    if (res) setPlotOverride({ ...tdaToPlotData(res), title: '持久性图谱' })
  }, [tda])

  const handleRunCode = useCallback(async (src: string) => {
    await compute.run(src)
  }, [compute])

  const handleAIOptimize = useCallback(async (code: string, _target: AuditTarget) => {
    return ai.optimize(code)
  }, [ai])

  const handleDrag = useCallback((dy: number) => {
    setRightSplit((prev) => Math.min(0.85, Math.max(0.15, prev + dy / window.innerHeight)))
  }, [])

  return (
    <TooltipProvider delayDuration={300}>
      <div className="flex flex-col h-screen bg-background overflow-hidden">

        {/* ── Title bar ── */}
        <div className="flex items-center gap-3 px-4 py-2 border-b border-border bg-card shrink-0">
          <div className="flex gap-1.5">
            <span className="h-3 w-3 rounded-full bg-red-500/70" />
            <span className="h-3 w-3 rounded-full bg-amber-500/70" />
            <span className="h-3 w-3 rounded-full bg-emerald-500/70" />
          </div>
          <span className="text-sm font-semibold text-foreground">SciCompute Assistant</span>
          <span className="text-xs text-muted-foreground ml-1 hidden sm:inline">
            Python 科学计算 · AI 辅助教学 · TDA 可视化
          </span>
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[11px] text-muted-foreground hidden md:inline">当前周次</span>
            <span className="text-[11px] font-bold text-violet-300 bg-violet-600/20 px-2 py-0.5 rounded">
              第 {selectedWeek} 周 · {currentWeek.module}
            </span>
          </div>
        </div>

        {/* ── Main area: Left + Center + Right ── */}
        <div className="flex flex-1 min-h-0">

          {/* Left: WeekSelector + CodeEditor */}
          <div className="w-[38%] min-w-[280px] flex flex-col overflow-hidden border-r border-border">
            <WeekSelector selectedWeek={selectedWeek} onWeekChange={handleWeekChange} />
            <div className="flex-1 min-h-0">
              <CodeEditor
                onCodeChange={(c) => { codeRef.current = c }}
                onAIOptimize={handleAIOptimize}
                onRunCode={handleRunCode}
                aiLoading={ai.loading}
                initialCode={currentWeek.demoCode}
              />
            </div>
          </div>

          {/* Center: Plotly + TDA */}
          <div className="flex-1 flex flex-col min-h-0 min-w-0 border-r border-border">
            <div className="overflow-hidden" style={{ height: `calc(${rightSplit * 100}% - 3px)` }}>
              <PlotlyViewer
                data={plotOverride?.data}
                layout={plotOverride?.layout}
                title={plotOverride?.title ?? 'Visualization'}
                isLoading={tda.loading}
                className="h-full"
              />
            </div>
            <VSplitter onDrag={handleDrag} />
            <div className="overflow-hidden" style={{ height: `calc(${(1 - rightSplit) * 100}% - 3px)` }}>
              <TDAInspector
                result={tda.result}
                loading={tda.loading}
                error={tda.error}
                onRun={handleTDArun}
                className="h-full"
              />
            </div>
          </div>

          {/* Right: Chat Panel */}
          <div className="w-[28%] min-w-[240px] flex flex-col overflow-hidden">
            <ChatPanel
              chat={chat}
              courseWeek={selectedWeek}
              weekTitle={`第 ${selectedWeek} 周 · ${currentWeek.title}`}
              aiPromptTemplate={aiLesson?.aiPromptTemplate}
            />
          </div>
        </div>

        {/* ── Compute output strip ── */}
        {(compute.result || compute.loading || compute.error) && (
          <div className={cn('border-t border-border bg-muted/20 px-4 py-2 max-h-28 overflow-y-auto shrink-0')}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-muted-foreground uppercase font-semibold tracking-wide">
                输出 · 第 {selectedWeek} 周
              </span>
              <button className="text-[10px] text-muted-foreground hover:text-foreground" onClick={compute.reset}>
                清除
              </button>
            </div>
            {compute.loading && <span className="text-[11px] text-sky-400 animate-pulse">运行中…</span>}
            {compute.error && <pre className="text-[11px] text-red-400 whitespace-pre-wrap">{compute.error}</pre>}
            {compute.result && (
              <>
                {compute.result.stdout && <pre className="text-[11px] text-foreground whitespace-pre-wrap">{compute.result.stdout}</pre>}
                {compute.result.stderr && <pre className="text-[11px] text-amber-400 whitespace-pre-wrap">{compute.result.stderr}</pre>}
                {!compute.result.ok && compute.result.error && <pre className="text-[11px] text-red-400 whitespace-pre-wrap">{compute.result.error}</pre>}
              </>
            )}
          </div>
        )}

        {/* ── Status bar ── */}
        <StatusBar
          status={apiStatus}
          aiLoading={ai.loading}
          tdaLoading={tda.loading}
          computeLoading={compute.loading}
          provider={provider}
          onToggleProvider={toggleProvider}
          onOpenSyllabus={() => setSyllabusOpen(true)}
        />

        {/* ── Syllabus modal ── */}
        <SyllabusInfo open={syllabusOpen} onClose={() => setSyllabusOpen(false)} />

      </div>
    </TooltipProvider>
  )
}
