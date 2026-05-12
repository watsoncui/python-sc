/**
 * PlotlyViewer – Plotly.js rendering area supporting 2D/3D plots.
 * Uses Plotly.js imperatively (Plotly.react / Plotly.newPlot) to avoid
 * react-plotly.js React 18/19 compatibility issues.
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import type { Data, Layout, Config } from 'plotly.js'
import { BarChart3, Box, ScatterChart, RefreshCw } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

// Dynamically import plotly.js-dist-min to keep initial bundle slim
async function getPlotly() {
  const mod = await import('plotly.js-dist-min')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (mod as any).default ?? mod
}

type PlotMode = '3d-scatter' | '2d-scatter' | 'surface' | 'persistence'

interface PlotlyViewerProps {
  data?: Data[]
  layout?: Partial<Layout>
  title?: string
  className?: string
  isLoading?: boolean
}

const BASE_LAYOUT: Partial<Layout> = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { color: '#9ca3af', size: 11 },
  margin: { l: 40, r: 20, t: 36, b: 40 },
  autosize: true,
}

const DARK_AXIS = { gridcolor: '#2e303a', zerolinecolor: '#4b5563' }

function makeDemoData(mode: PlotMode): { data: Data[]; layout: Partial<Layout> } {
  if (mode === '3d-scatter') {
    const n = 300
    const t = Array.from({ length: n }, (_, i) => (i / n) * Math.PI * 6)
    return {
      data: [
        {
          type: 'scatter3d',
          mode: 'markers',
          x: t.map((v) => Math.cos(v) * (1 + 0.3 * Math.sin(7 * v))),
          y: t.map((v) => Math.sin(v) * (1 + 0.3 * Math.cos(7 * v))),
          z: t.map((v) => v / 6),
          marker: { size: 3, color: t, colorscale: 'Viridis', opacity: 0.85 },
        } as Data,
      ],
      layout: {
        ...BASE_LAYOUT,
        scene: {
          xaxis: DARK_AXIS,
          yaxis: DARK_AXIS,
          zaxis: DARK_AXIS,
          bgcolor: 'rgba(0,0,0,0)',
        },
        title: { text: '3D 点云预览 (示例)', font: { size: 12 } },
      },
    }
  }

  if (mode === 'surface') {
    const size = 30
    const x = Array.from({ length: size }, (_, i) => (i / size) * 4 - 2)
    const y = x
    const z = x.map((xi) => y.map((yi) => Math.sin(xi * xi + yi * yi)))
    return {
      data: [{ type: 'surface', x, y, z, colorscale: 'Plasma', opacity: 0.9 } as Data],
      layout: {
        ...BASE_LAYOUT,
        scene: {
          xaxis: DARK_AXIS,
          yaxis: DARK_AXIS,
          zaxis: DARK_AXIS,
          bgcolor: 'rgba(0,0,0,0)',
        },
        title: { text: '3D 曲面演示 sin(x²+y²)', font: { size: 12 } },
      },
    }
  }

  if (mode === 'persistence') {
    const pts = Array.from({ length: 50 }, () => {
      const x = Math.random() * 0.8
      return { x, y: x + Math.random() * 0.5 + 0.05 }
    })
    return {
      data: [
        {
          type: 'scatter',
          mode: 'markers',
          x: pts.map((p) => p.x),
          y: pts.map((p) => p.y),
          name: 'H₁',
          marker: { color: '#a78bfa', size: 6 },
        } as Data,
        {
          type: 'scatter',
          mode: 'lines',
          x: [0, 1],
          y: [0, 1],
          line: { color: '#4b5563', dash: 'dash', width: 1 },
          showlegend: false,
        } as Data,
      ],
      layout: {
        ...BASE_LAYOUT,
        xaxis: { ...DARK_AXIS, title: { text: 'Birth' } },
        yaxis: { ...DARK_AXIS, title: { text: 'Death' } },
        legend: { font: { size: 10 } },
        title: { text: '持久性图谱 (示例)', font: { size: 12 } },
      },
    }
  }

  // 2d-scatter
  const n = 100
  return {
    data: [
      {
        type: 'scatter',
        mode: 'markers',
        x: Array.from({ length: n }, () => Math.random()),
        y: Array.from({ length: n }, () => Math.random()),
        marker: { color: '#7c3aed', size: 5, opacity: 0.7 },
      } as Data,
    ],
    layout: {
      ...BASE_LAYOUT,
      xaxis: DARK_AXIS,
      yaxis: DARK_AXIS,
      title: { text: '2D 散点图 (示例)', font: { size: 12 } },
    },
  }
}

const PLOT_CONFIG: Partial<Config> = {
  displayModeBar: true,
  modeBarButtonsToRemove: ['sendDataToCloud', 'toImage'],
  displaylogo: false,
  responsive: true,
}

const modeLabels: Record<PlotMode, { icon: React.ReactNode; label: string }> = {
  '3d-scatter': { icon: <Box className="h-3.5 w-3.5" />, label: '3D 点云' },
  surface: { icon: <BarChart3 className="h-3.5 w-3.5" />, label: '3D 曲面' },
  '2d-scatter': { icon: <ScatterChart className="h-3.5 w-3.5" />, label: '2D 散点' },
  persistence: { icon: <ScatterChart className="h-3.5 w-3.5" />, label: '持久性图' },
}

export function PlotlyViewer({
  data,
  layout,
  title,
  className,
  isLoading = false,
}: PlotlyViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [mode, setMode] = useState<PlotMode>('3d-scatter')
  const plotRef = useRef<HTMLDivElement>(null)
  const renderedRef = useRef(false)

  const render = useCallback(async () => {
    const el = plotRef.current
    if (!el) return
    const Plotly = await getPlotly()
    const demo = makeDemoData(mode)
    const plotData = data ?? demo.data
    const plotLayout: Partial<Layout> = {
      ...(layout ?? demo.layout),
      width: el.clientWidth || undefined,
      height: el.clientHeight || undefined,
    }
    if (renderedRef.current) {
      await Plotly.react(el, plotData, plotLayout, PLOT_CONFIG)
    } else {
      await Plotly.newPlot(el, plotData, plotLayout, PLOT_CONFIG)
      renderedRef.current = true
    }
  }, [data, layout, mode])

  // Re-render when data/mode change
  useEffect(() => {
    render()
  }, [render])

  // Resize observer
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(() => {
      if (plotRef.current && renderedRef.current) {
        getPlotly().then((Plotly) => {
          Plotly.Plots?.resize(plotRef.current!)
        })
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  return (
    <div className={cn('flex h-full flex-col bg-card', className)}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-3 py-2 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-foreground tracking-wide uppercase">
            {title ?? 'Visualization'}
          </span>
          {isLoading && <RefreshCw className="h-3 w-3 text-violet-400 animate-spin" />}
        </div>
        {!data && (
          <div className="flex gap-1">
            {(Object.entries(modeLabels) as [PlotMode, { icon: React.ReactNode; label: string }][]).map(
              ([m, { icon, label }]) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={cn(
                    'flex items-center gap-1 px-2 py-0.5 rounded text-[10px] transition-colors',
                    mode === m
                      ? 'bg-violet-600/30 text-violet-300'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted',
                  )}
                >
                  {icon}
                  {label}
                </button>
              ),
            )}
          </div>
        )}
        {data && (
          <Badge variant="success" className="text-[10px]">
            来自 API
          </Badge>
        )}
      </div>

      {/* Plot area */}
      <div ref={containerRef} className="flex-1 min-h-0 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-card/80 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-3">
              <RefreshCw className="h-6 w-6 text-violet-400 animate-spin" />
              <span className="text-xs text-muted-foreground">计算中…</span>
            </div>
          </div>
        )}
        <div ref={plotRef} className="w-full h-full" />
      </div>
    </div>
  )
}
