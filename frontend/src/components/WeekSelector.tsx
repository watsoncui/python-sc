/**
 * WeekSelector – course week picker with inline topic summary.
 * Allows students to navigate between the 18 course weeks.
 * Wires into the AI audit hook via the `courseWeek` prop.
 */
import { useState } from 'react'
import { ChevronDown, ChevronUp, BookOpen, Bot, Cpu, Sigma, BarChart2, FlaskConical } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import WEEKS from '@/data/syllabusWeeks'
import type { WeekData, LessonLevel } from '@/data/syllabusWeeks'
import { cn } from '@/lib/utils'

interface WeekSelectorProps {
  selectedWeek: number
  onWeekChange: (week: number) => void
}

const MODULE_ICONS: Record<string, React.ReactNode> = {
  '工具与基础':   <Cpu className="h-3.5 w-3.5" />,
  'NumPy':        <Sigma className="h-3.5 w-3.5" />,
  '误差与线性代数': <Sigma className="h-3.5 w-3.5" />,
  '线性代数':     <Sigma className="h-3.5 w-3.5" />,
  '插值':         <BarChart2 className="h-3.5 w-3.5" />,
  '数值微积分':   <BarChart2 className="h-3.5 w-3.5" />,
  'ODE':          <BarChart2 className="h-3.5 w-3.5" />,
  'ODE + 优化':   <BarChart2 className="h-3.5 w-3.5" />,
  '优化 + 可视化': <BarChart2 className="h-3.5 w-3.5" />,
  'AI 辅助':      <Bot className="h-3.5 w-3.5" />,
  'PDE':          <FlaskConical className="h-3.5 w-3.5" />,
  '反问题 + UQ':  <FlaskConical className="h-3.5 w-3.5" />,
  '可微编程':     <Bot className="h-3.5 w-3.5" />,
  '科学 ML':      <Bot className="h-3.5 w-3.5" />,
  '高性能':       <Cpu className="h-3.5 w-3.5" />,
  '文献导读':     <BookOpen className="h-3.5 w-3.5" />,
  '并行 + 工程化': <Cpu className="h-3.5 w-3.5" />,
  '项目':         <BookOpen className="h-3.5 w-3.5" />,
}

const LEVEL_VARIANT: Record<LessonLevel, 'success' | 'secondary' | 'destructive'> = {
  B: 'success',
  H: 'secondary',
  C: 'destructive',
}

function WeekCard({
  week,
  isSelected,
  onClick,
}: {
  week: WeekData
  isSelected: boolean
  onClick: () => void
}) {
  const icon = MODULE_ICONS[week.module] ?? <BookOpen className="h-3.5 w-3.5" />
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left px-2 py-1.5 rounded-md transition-colors flex items-start gap-2',
        isSelected
          ? 'bg-violet-600/25 border border-violet-500/40 text-violet-200'
          : 'hover:bg-muted/60 text-muted-foreground hover:text-foreground border border-transparent',
      )}
    >
      <span
        className={cn(
          'text-[10px] font-mono shrink-0 mt-0.5 w-4 text-right',
          isSelected ? 'text-violet-400' : 'text-muted-foreground',
        )}
      >
        {week.week}
      </span>
      <span className={cn('shrink-0 mt-0.5', isSelected ? 'text-violet-400' : 'text-muted-foreground')}>
        {icon}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-[11px] font-medium leading-tight truncate">{week.title}</p>
        <p className={cn('text-[10px] leading-tight', isSelected ? 'text-violet-300/70' : 'text-muted-foreground/60')}>
          {week.module}
        </p>
      </div>
    </button>
  )
}

function LessonRow({ lesson }: { lesson: WeekData['lessons'][number] }) {
  return (
    <div className="flex items-start gap-2 py-1 border-t border-border/40">
      <span className="text-[10px] font-mono text-muted-foreground w-6 shrink-0">{lesson.id}</span>
      <p className="text-[11px] text-foreground flex-1 leading-snug">{lesson.title}</p>
      <div className="flex items-center gap-1 shrink-0">
        {lesson.hasAI && (
          <Badge variant="secondary" className="text-[9px] px-1 py-0 h-4 bg-violet-900/50 text-violet-300">
            AI
          </Badge>
        )}
        <Badge variant={LEVEL_VARIANT[lesson.level]} className="text-[9px] px-1 py-0 h-4">
          {lesson.level}
        </Badge>
      </div>
    </div>
  )
}

export function WeekSelector({ selectedWeek, onWeekChange }: WeekSelectorProps) {
  const [listOpen, setListOpen] = useState(false)
  const current = WEEKS.find((w) => w.week === selectedWeek) ?? WEEKS[0]

  return (
    <div className="flex flex-col border-b border-border">
      {/* Current week header (always visible) */}
      <button
        onClick={() => setListOpen((v) => !v)}
        className="flex items-center gap-2 px-3 py-2 hover:bg-muted/30 transition-colors"
      >
        <div className="h-5 w-5 rounded bg-violet-600/30 flex items-center justify-center shrink-0">
          <span className="text-[10px] font-bold text-violet-300">{selectedWeek}</span>
        </div>
        <div className="flex-1 min-w-0 text-left">
          <p className="text-xs font-semibold text-foreground leading-tight truncate">
            第 {selectedWeek} 周 · {current.title}
          </p>
          <p className="text-[10px] text-muted-foreground">{current.module}</p>
        </div>
        {listOpen ? (
          <ChevronUp className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        )}
      </button>

      {/* Expanded week list */}
      {listOpen && (
        <div className="border-t border-border bg-card max-h-60 overflow-y-auto px-2 py-1 space-y-0.5">
          {WEEKS.map((w) => (
            <WeekCard
              key={w.week}
              week={w}
              isSelected={w.week === selectedWeek}
              onClick={() => {
                onWeekChange(w.week)
                setListOpen(false)
              }}
            />
          ))}
        </div>
      )}

      {/* Current week lesson breakdown */}
      <div className="px-3 pb-2 pt-1">
        {current.lessons.map((lesson) => (
          <LessonRow key={lesson.id} lesson={lesson} />
        ))}
        {/* Context tags */}
        <div className="flex flex-wrap gap-1 mt-1.5 pt-1.5 border-t border-border/30">
          {current.contextTags.slice(1).map((tag) => (
            <span
              key={tag}
              className="text-[9px] bg-muted/50 text-muted-foreground rounded px-1.5 py-0.5"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
