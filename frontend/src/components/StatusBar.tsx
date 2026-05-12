/**
 * StatusBar – bottom bar showing API connection, provider mode toggle,
 * latency, active tasks, and app version.
 */
import { Wifi, WifiOff, Loader2, Server, Laptop, Clock, RefreshCw, BookOpen } from 'lucide-react'
import type { ApiStatus } from '@/hooks/useApiStatus'
import type { ProviderMode } from '@/api/types'
import { cn } from '@/lib/utils'

interface StatusBarProps {
  status: ApiStatus
  computeLoading?: boolean
  aiLoading?: boolean
  tdaLoading?: boolean
  provider?: ProviderMode
  onToggleProvider?: () => void
  onOpenSyllabus?: () => void
}

function LatencyDot({ ms }: { ms: number }) {
  const color = ms < 100 ? 'bg-emerald-400' : ms < 500 ? 'bg-amber-400' : 'bg-red-400'
  return <span className={cn('inline-block h-1.5 w-1.5 rounded-full', color)} />
}

export function StatusBar({
  status,
  computeLoading,
  aiLoading,
  tdaLoading,
  provider = 'server',
  onToggleProvider,
  onOpenSyllabus,
}: StatusBarProps) {
  const { connection, mode, latencyMs, version, lastChecked, refresh } = status
  const isOnline = connection === 'online'
  const isConnecting = connection === 'connecting'

  return (
    <div className="flex h-7 items-center gap-3 border-t border-border bg-muted/30 px-3 shrink-0 select-none overflow-hidden">
      {/* Syllabus shortcut */}
      {onOpenSyllabus && (
        <>
          <button
            onClick={onOpenSyllabus}
            title="课程大纲"
            className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            <BookOpen className="h-3 w-3" />
            <span className="hidden sm:inline">课程信息</span>
          </button>
          <span className="text-border">│</span>
        </>
      )}

      {/* Connection status */}
      <div className="flex items-center gap-1.5">
        {isConnecting && (
          <><Loader2 className="h-3 w-3 text-muted-foreground animate-spin" /><span className="text-[11px] text-muted-foreground">连接中…</span></>
        )}
        {isOnline && (
          <><Wifi className="h-3 w-3 text-emerald-400" /><span className="text-[11px] text-emerald-400">已连接</span></>
        )}
        {connection === 'offline' && (
          <><WifiOff className="h-3 w-3 text-red-400" /><span className="text-[11px] text-red-400">离线</span></>
        )}
      </div>

      <span className="text-border">│</span>

      {/* Provider mode toggle */}
      <button
        onClick={onToggleProvider}
        className="flex items-center gap-1.5 hover:opacity-80 transition-opacity"
        title={`当前: ${provider === 'server' ? 'Server 模式（教师 API Key）' : 'Local 模式（自备 API Key）'}，点击切换`}
      >
        {provider === 'server'
          ? <Server className="h-3 w-3 text-violet-400" />
          : <Laptop className="h-3 w-3 text-sky-400" />}
        <span className={cn('text-[11px] font-medium',
          provider === 'server' ? 'text-violet-400' : 'text-sky-400')}>
          {provider === 'server' ? 'Server' : 'Local'}
        </span>
        {/* Backend-reported mode may differ – show if mismatch */}
        {mode !== provider && (
          <span className="text-[9px] text-amber-400">({mode})</span>
        )}
      </button>

      {/* Latency */}
      {latencyMs !== null && (
        <>
          <span className="text-border">│</span>
          <div className="flex items-center gap-1.5">
            <LatencyDot ms={latencyMs} />
            <Clock className="h-3 w-3 text-muted-foreground" />
            <span className="text-[11px] text-muted-foreground font-mono">{latencyMs} ms</span>
          </div>
        </>
      )}

      <span className="text-border">│</span>

      {/* Active tasks */}
      <div className="flex items-center gap-2">
        {aiLoading && (
          <span className="flex items-center gap-1 text-[11px] text-violet-400">
            <Loader2 className="h-3 w-3 animate-spin" />AI
          </span>
        )}
        {tdaLoading && (
          <span className="flex items-center gap-1 text-[11px] text-amber-400">
            <Loader2 className="h-3 w-3 animate-spin" />TDA
          </span>
        )}
        {computeLoading && (
          <span className="flex items-center gap-1 text-[11px] text-sky-400">
            <Loader2 className="h-3 w-3 animate-spin" />执行
          </span>
        )}
        {!aiLoading && !tdaLoading && !computeLoading && (
          <span className="text-[11px] text-muted-foreground">就绪</span>
        )}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {lastChecked && (
        <span className="text-[10px] text-muted-foreground hidden sm:inline">
          {lastChecked.toLocaleTimeString()}
        </span>
      )}

      <button
        onClick={refresh}
        disabled={isConnecting}
        title="刷新连接状态"
        className="text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"
      >
        <RefreshCw className="h-3 w-3" />
      </button>

      <span className="text-border">│</span>
      <span className="text-[10px] text-muted-foreground">SciCompute {version}</span>
    </div>
  )
}
