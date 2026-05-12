/**
 * SyllabusInfo – modal/panel showing course objectives, AI policy, and assessment.
 * Driven by syllabus.md content.
 */
import { useState } from 'react'
import { BookOpen, X, CheckCircle, AlertTriangle, XCircle, GraduationCap, Bot, BarChart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

interface SyllabusInfoProps {
  /** controlled open state */
  open: boolean
  onClose: () => void
}

// ── Data extracted from syllabus.md ─────────────────────────────────────────

const OBJECTIVES = [
  {
    icon: <Bot className="h-4 w-4 text-violet-400" />,
    title: '工具能力',
    body: '掌握以 Python 为核心的科学计算工具链（uv/conda、Jupyter、NumPy、SciPy、Matplotlib），能独立搭建可复现的计算环境并完成小型项目。',
  },
  {
    icon: <BarChart className="h-4 w-4 text-emerald-400" />,
    title: '数学实现',
    body: '能将已修数学课程中的数值方法（线性代数、微积分、ODE、优化等）转化为可运行、可验证的代码，并理解误差与稳定性等基本概念。',
  },
  {
    icon: <GraduationCap className="h-4 w-4 text-amber-400" />,
    title: '层次递进',
    body: '在「基础 → 高阶 → 挑战」模块下，逐步接触 PDE、反问题/UQ、可微编程与科学机器学习，形成由浅入深的完整路径。',
  },
  {
    icon: <Bot className="h-4 w-4 text-sky-400" />,
    title: 'AI 与现代化',
    body: '在多个核心模块中引入 AI 辅助（提示/代码生成/结果验证/文档查阅），培养「会用人机协作、更会验证与批判」的习惯；不回避深度学习在科学计算中的应用。',
  },
]

const AI_POLICIES = [
  {
    type: 'allow' as const,
    icon: <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />,
    label: '允许',
    items: [
      '在课后作业、阅读文档、调试代码时使用大语言模型等 AI 工具',
      '用 AI 生成代码草稿、解释报错、改进提示词',
      '在作业或项目中使用 AI 辅助（须注明「何处使用了 AI、如何验证与修改」）',
    ],
  },
  {
    type: 'require' as const,
    icon: <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />,
    label: '要求',
    items: [
      '提交的代码必须本人能逐行解释并根据要求修改',
      '凡使用了 AI 辅助，须在 Notebook 中简要说明与验证方式',
      '平时作业若发现整段照搬且无法说明与验证，将按学术不端处理',
    ],
  },
  {
    type: 'prohibit' as const,
    icon: <XCircle className="h-3.5 w-3.5 text-red-400" />,
    label: '禁止',
    items: [
      '直接提交无法理解的生成结果',
      '不注明 AI 使用且无法解释代码',
    ],
  },
]

const ASSESSMENT = {
  components: [
    { label: '平时作业', weight: '40%', desc: '基于 Jupyter 的课后作业（含代码、文字说明与 AI 使用说明）' },
    { label: '期末项目', weight: '60%', desc: '第 11 周布置，第 18 周提交；Notebook 形式含环境说明；第 18 周课堂展示' },
  ],
  notes: [
    '无笔试、无上机考试',
    '期末项目在讲完 AI 辅助（第 11 周）后布置，附一页纸 handout',
    '项目不及格时补考形式为项目重做或重新提交（按校历公布）',
    '第 19 周无授课安排',
  ],
}

const STACK_WEEKS = [
  { weeks: '第 1-6 周',   tags: ['NumPy', 'SciPy', '线性代数', '插值', '拟合', '数值积分'],    level: 'B', color: 'text-emerald-400' },
  { weeks: '第 7-10 周',  tags: ['ODE', '求根', '优化', 'Matplotlib', 'AI辅助'],               level: 'B+H', color: 'text-amber-400' },
  { weeks: '第 11-13 周', tags: ['PDE', '反问题', 'UQ', 'JAX', '自动微分'],                    level: 'H', color: 'text-orange-400' },
  { weeks: '第 14 周',    tags: ['PINN', 'Neural ODE', 'SciML'],                               level: 'H/C', color: 'text-red-400' },
  { weeks: '第 15-17 周', tags: ['Numba/Cython', 'GPU', 'Dask', '并行', '工程化'],             level: 'H', color: 'text-violet-400' },
  { weeks: '第 18 周',    tags: ['项目展示', '总结'],                                           level: 'C', color: 'text-sky-400' },
]

export function SyllabusInfo({ open, onClose }: SyllabusInfoProps) {
  const [tab, setTab] = useState<'objectives' | 'ai-policy' | 'assessment' | 'structure'>('objectives')

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative z-10 bg-card border border-border rounded-xl shadow-2xl w-[540px] max-w-[95vw] max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border shrink-0">
          <div className="h-8 w-8 rounded-full bg-violet-600/30 flex items-center justify-center">
            <BookOpen className="h-4 w-4 text-violet-300" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">Python 科学计算</h2>
            <p className="text-[11px] text-muted-foreground">课程大纲 · 58 课时 · 18 周</p>
          </div>
          <Button variant="ghost" size="icon" className="ml-auto h-7 w-7" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border px-4 shrink-0">
          {[
            { id: 'objectives', label: '课程目标' },
            { id: 'ai-policy',  label: 'AI 政策' },
            { id: 'assessment', label: '考核' },
            { id: 'structure',  label: '内容结构' },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id as typeof tab)}
              className={cn(
                'px-3 py-2 text-[12px] border-b-2 transition-colors',
                tab === t.id
                  ? 'border-violet-500 text-violet-300'
                  : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
            >
              {t.label}
            </button>
          ))}
        </div>

        <ScrollArea className="flex-1 px-4 py-3">
          {/* ── 课程目标 ── */}
          {tab === 'objectives' && (
            <div className="space-y-3">
              <p className="text-[11px] text-muted-foreground">
                面向数学学院二年级、三年级本科生。先修：数学分析、线性代数（必须）；ODE、数值分析（建议）；一年级已修 C++。
              </p>
              {OBJECTIVES.map((obj, i) => (
                <div key={i} className="flex items-start gap-3 bg-muted/20 rounded-lg px-3 py-2">
                  <div className="shrink-0 mt-0.5">{obj.icon}</div>
                  <div>
                    <p className="text-xs font-medium text-foreground">{obj.title}</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">{obj.body}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── AI 政策 ── */}
          {tab === 'ai-policy' && (
            <div className="space-y-3">
              <p className="text-[11px] text-muted-foreground">
                本课鼓励 AI 辅助，但要求「会用人机协作，更会验证与批判」。
              </p>
              {AI_POLICIES.map((policy) => (
                <div key={policy.type} className={cn(
                  'rounded-lg border px-3 py-2',
                  policy.type === 'allow'    && 'bg-emerald-900/15 border-emerald-700/30',
                  policy.type === 'require'  && 'bg-amber-900/15 border-amber-700/30',
                  policy.type === 'prohibit' && 'bg-red-900/15 border-red-700/30',
                )}>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    {policy.icon}
                    <span className={cn('text-[11px] font-semibold',
                      policy.type === 'allow'    && 'text-emerald-300',
                      policy.type === 'require'  && 'text-amber-300',
                      policy.type === 'prohibit' && 'text-red-300',
                    )}>
                      {policy.label}
                    </span>
                  </div>
                  <ul className="space-y-1">
                    {policy.items.map((item, i) => (
                      <li key={i} className="text-[11px] text-muted-foreground flex items-start gap-1.5">
                        <span className="shrink-0 mt-0.5">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}

          {/* ── 考核 ── */}
          {tab === 'assessment' && (
            <div className="space-y-3">
              {ASSESSMENT.components.map((comp) => (
                <div key={comp.label} className="bg-muted/20 rounded-lg px-3 py-2.5 flex items-start gap-3">
                  <div className="text-center shrink-0">
                    <p className="text-xl font-bold text-violet-300">{comp.weight}</p>
                    <p className="text-[10px] text-muted-foreground">{comp.label}</p>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1 leading-relaxed">{comp.desc}</p>
                </div>
              ))}
              <div className="border border-border/60 rounded-lg px-3 py-2">
                <p className="text-[11px] font-medium text-foreground mb-1.5">注意事项</p>
                {ASSESSMENT.notes.map((note, i) => (
                  <p key={i} className="text-[11px] text-muted-foreground flex items-start gap-1.5 mb-1">
                    <span className="shrink-0">•</span>{note}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* ── 内容结构 ── */}
          {tab === 'structure' && (
            <div className="space-y-2">
              <div className="flex gap-3 mb-3">
                {[
                  { label: 'B 基础', pct: '~60%', color: 'text-emerald-400' },
                  { label: 'H 高阶', pct: '~30%', color: 'text-amber-400' },
                  { label: 'C 挑战', pct: '~10%', color: 'text-red-400' },
                ].map((item) => (
                  <div key={item.label} className="bg-muted/20 rounded-lg px-3 py-2 flex-1 text-center">
                    <p className={cn('text-sm font-bold', item.color)}>{item.pct}</p>
                    <p className="text-[10px] text-muted-foreground">{item.label}</p>
                  </div>
                ))}
              </div>
              {STACK_WEEKS.map((row) => (
                <div key={row.weeks} className="bg-muted/20 rounded-lg px-3 py-2">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-[11px] font-medium text-foreground">{row.weeks}</span>
                    <Badge variant="muted" className={cn('text-[9px] px-1', row.color)}>{row.level}</Badge>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {row.tags.map((tag) => (
                      <span key={tag} className="text-[10px] bg-muted/50 text-muted-foreground rounded px-1.5 py-0.5">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  )
}
