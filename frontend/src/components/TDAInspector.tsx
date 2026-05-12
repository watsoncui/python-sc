/**
 * TDAInspector – displays the TDA persistence diagram metadata,
 * Betti numbers, and filtration statistics returned by the backend.
 * Also exposes controls to trigger a fresh TDA pipeline run.
 */
import { useState, useMemo } from 'react'
import { Activity, ChevronDown, ChevronRight, AlertTriangle, Info, Sigma, SlidersHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { TDAResponse, PersistencePoint, BettiCurve } from '@/api/types'
import { cn } from '@/lib/utils'

interface TDAInspectorProps {
  result: TDAResponse | null
  loading?: boolean
  error?: string | null
  onRun?: () => void
  className?: string
}

const DIM_COLORS: Record<number, string> = {
  0: 'text-emerald-400',
  1: 'text-violet-400',
  2: 'text-amber-400',
  3: 'text-rose-400',
}

const DIM_BG: Record<number, string> = {
  0: 'bg-emerald-900/40',
  1: 'bg-violet-900/40',
  2: 'bg-amber-900/40',
  3: 'bg-rose-900/40',
}

function formatNum(n: number, dec = 4) {
  return Number.isFinite(n) ? n.toFixed(dec) : '∞'
}

function StatRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-2 py-0.5">
      <span className="text-[11px] text-muted-foreground shrink-0">{label}</span>
      <span className={cn('text-[11px] text-foreground truncate', mono && 'font-mono')}>
        {value}
      </span>
    </div>
  )
}

function BettiSection({ curves }: { curves: BettiCurve[] }) {
  const [open, setOpen] = useState(true)
  return (
    <div className="border border-border/60 rounded-md overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-1.5 bg-muted/20 hover:bg-muted/40 transition-colors"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
        )}
        <Sigma className="h-3.5 w-3.5 text-violet-400" />
        <span className="text-xs font-medium">Betti 曲线</span>
        <Badge variant="muted" className="ml-auto text-[10px]">
          {curves.length} 维
        </Badge>
      </button>
      {open && (
        <div className="px-3 py-2 space-y-2">
          {curves.map((c) => (
            <div key={c.dimension}>
              <div className="flex items-center gap-1.5 mb-1">
                <span className={cn('text-[11px] font-semibold', DIM_COLORS[c.dimension] ?? 'text-foreground')}>
                  H{c.dimension}
                </span>
                <span className="text-[10px] text-muted-foreground">
                  max β={Math.max(...c.values)}
                </span>
              </div>
              {/* Tiny inline sparkline */}
              <div className="flex items-end gap-[1px] h-6">
                {c.values
                  .filter((_, i) => i % Math.ceil(c.values.length / 40) === 0)
                  .map((v, i) => {
                    const maxV = Math.max(...c.values, 1)
                    const h = Math.max(1, Math.round((v / maxV) * 24))
                    return (
                      <div
                        key={i}
                        style={{ height: h }}
                        className={cn('w-1 rounded-sm opacity-70', DIM_BG[c.dimension] ?? 'bg-muted')}
                      />
                    )
                  })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PointsSection({ points }: { points: PersistencePoint[] }) {
  const [open, setOpen] = useState(true)
  const [dimFilter, setDimFilter] = useState<number | null>(null)

  const dims = [...new Set(points.map((p) => p.dimension))].sort()
  const filtered = dimFilter === null ? points : points.filter((p) => p.dimension === dimFilter)
  const sorted = [...filtered].sort((a, b) => b.persistence - a.persistence).slice(0, 30)

  return (
    <div className="border border-border/60 rounded-md overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-1.5 bg-muted/20 hover:bg-muted/40 transition-colors"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
        )}
        <Activity className="h-3.5 w-3.5 text-violet-400" />
        <span className="text-xs font-medium">持久性点</span>
        <Badge variant="muted" className="ml-auto text-[10px]">
          {points.length}
        </Badge>
      </button>
      {open && (
        <div className="px-3 py-2">
          {/* Dimension filter */}
          <div className="flex gap-1 mb-2 flex-wrap">
            <button
              onClick={() => setDimFilter(null)}
              className={cn(
                'px-2 py-0.5 rounded text-[10px] transition-colors',
                dimFilter === null
                  ? 'bg-violet-600/30 text-violet-300'
                  : 'text-muted-foreground hover:bg-muted',
              )}
            >
              全部
            </button>
            {dims.map((d) => (
              <button
                key={d}
                onClick={() => setDimFilter(d)}
                className={cn(
                  'px-2 py-0.5 rounded text-[10px] transition-colors',
                  dimFilter === d
                    ? 'bg-violet-600/30 text-violet-300'
                    : 'text-muted-foreground hover:bg-muted',
                )}
              >
                H{d}
              </button>
            ))}
          </div>
          {/* Table */}
          <div className="w-full">
            <div className="grid grid-cols-4 gap-1 text-[10px] text-muted-foreground pb-1 border-b border-border/50">
              <span>维度</span>
              <span>birth</span>
              <span>death</span>
              <span>persist.</span>
            </div>
            {sorted.map((p, i) => (
              <div
                key={i}
                className="grid grid-cols-4 gap-1 text-[10px] py-0.5 border-b border-border/20 hover:bg-muted/20"
              >
                <span className={cn('font-semibold', DIM_COLORS[p.dimension] ?? 'text-foreground')}>
                  H{p.dimension}
                </span>
                <span className="font-mono">{formatNum(p.birth, 3)}</span>
                <span className="font-mono">
                  {p.death === Infinity || p.death > 1e6 ? '∞' : formatNum(p.death, 3)}
                </span>
                <span className="font-mono">{formatNum(p.persistence, 3)}</span>
              </div>
            ))}
            {sorted.length < filtered.length && (
              <p className="text-[10px] text-muted-foreground pt-1 text-center">
                显示前 {sorted.length}/{filtered.length} 个
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function TDAInspector({
  result,
  loading = false,
  error = null,
  onRun,
  className,
}: TDAInspectorProps) {
  const [minPersistence, setMinPersistence] = useState(0)

  // Compute max persistence to set slider range
  const maxPersistenceValue = useMemo(() => {
    if (!result) return 1
    const vals = result.diagram.points
      .map((p) => p.persistence)
      .filter((v) => Number.isFinite(v) && v < 1e6)
    return vals.length ? Math.max(...vals) : 1
  }, [result])

  const filteredPoints = useMemo(() => {
    if (!result) return []
    return result.diagram.points.filter((p) => p.persistence >= minPersistence)
  }, [result, minPersistence])

  return (
    <div className={cn('flex h-full flex-col bg-card border-t border-border', className)}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-3 py-2 shrink-0">
        <div className="flex items-center gap-2">
          <Activity className="h-3.5 w-3.5 text-violet-400" />
          <span className="text-xs font-semibold text-foreground tracking-wide uppercase">
            TDA 拓扑检查器
          </span>
          {result && (
            <Badge variant="muted" className="text-[10px]">
              {result.backend}
            </Badge>
          )}
        </div>
        {onRun && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRun}
            disabled={loading}
            className="h-6 text-[10px] px-2"
          >
            {loading ? '计算中…' : '运行 TDA'}
          </Button>
        )}
      </div>

      <ScrollArea className="flex-1">
        <div className="px-3 py-3 space-y-3">
          {/* Error state */}
          {error && (
            <div className="flex items-start gap-2 p-2 rounded-md bg-destructive/10 border border-destructive/30">
              <AlertTriangle className="h-3.5 w-3.5 text-destructive shrink-0 mt-0.5" />
              <p className="text-[11px] text-destructive">{error}</p>
            </div>
          )}

          {/* Empty state */}
          {!result && !loading && !error && (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <div className="h-10 w-10 rounded-full bg-violet-900/30 flex items-center justify-center">
                <Activity className="h-5 w-5 text-violet-400" />
              </div>
              <div className="text-center">
                <p className="text-xs font-medium text-foreground">暂无拓扑数据</p>
                <p className="text-[11px] text-muted-foreground mt-1">
                  在编辑器中运行代码或点击「运行 TDA」
                </p>
              </div>
              {onRun && (
                <Button variant="outline" size="sm" onClick={onRun} className="text-xs">
                  开始分析
                </Button>
              )}
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-8 gap-2">
              <div className="h-8 w-8 rounded-full border-2 border-violet-500/30 border-t-violet-500 animate-spin" />
              <p className="text-xs text-muted-foreground">TDA 流水线运行中…</p>
            </div>
          )}

          {/* Result */}
          {result && !loading && (
            <>
              {/* Summary stats */}
              <div className="border border-border/60 rounded-md px-3 py-2 space-y-0.5">
                <div className="flex items-center gap-1.5 mb-1">
                  <Info className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs font-medium">摘要</span>
                </div>
                <StatRow label="后端" value={result.backend} />
                <StatRow label="耗时" value={`${result.elapsed_ms.toFixed(1)} ms`} mono />
                <StatRow
                  label="持久性点总数"
                  value={String(result.diagram.points.length)}
                  mono
                />
                <StatRow
                  label="最大滤波参数"
                  value={formatNum(result.diagram.max_filtration)}
                  mono
                />
                <StatRow label="坐标轴范围" value={result.diagram.axis_limits.join(' – ')} mono />
                <StatRow label="坐标轴缩放" value={result.diagram.scale} />
              </div>

              {/* Warnings */}
              {result.warnings.length > 0 && (
                <div className="space-y-1">
                  {result.warnings.map((w, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 p-2 rounded bg-amber-900/20 border border-amber-700/30"
                    >
                      <AlertTriangle className="h-3 w-3 text-amber-400 shrink-0 mt-0.5" />
                      <p className="text-[10px] text-amber-300">{w}</p>
                    </div>
                  ))}
                </div>
              )}

                  {/* Persistence filter slider */}
              {maxPersistenceValue > 0 && (
                <div className="border border-border/60 rounded-md px-3 py-2">
                  <div className="flex items-center gap-2 mb-1.5">
                    <SlidersHorizontal className="h-3.5 w-3.5 text-violet-400" />
                    <span className="text-xs font-medium">Persistence 过滤</span>
                    <span className="ml-auto text-[10px] font-mono text-muted-foreground">
                      ≥ {minPersistence.toFixed(3)}
                    </span>
                    <Badge variant="muted" className="text-[9px] px-1">
                      {filteredPoints.length}/{result.diagram.points.length}
                    </Badge>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={maxPersistenceValue}
                    step={maxPersistenceValue / 100}
                    value={minPersistence}
                    onChange={(e) => setMinPersistence(parseFloat(e.target.value))}
                    className="w-full accent-violet-500 h-1.5"
                  />
                  <div className="flex justify-between mt-0.5">
                    <span className="text-[9px] text-muted-foreground">0</span>
                    <span className="text-[9px] text-muted-foreground">{maxPersistenceValue.toFixed(3)}</span>
                  </div>
                </div>
              )}

              {/* Betti curves */}
              {result.diagram.betti_curves.length > 0 && (
                <BettiSection curves={result.diagram.betti_curves} />
              )}

              {/* Persistence points table (filtered) */}
              {filteredPoints.length > 0 && (
                <PointsSection points={filteredPoints} />
              )}
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
