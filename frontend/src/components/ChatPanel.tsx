/**
 * ChatPanel – teaching chat interface backed by /ai/chat.
 * Follows the "先回答→后推导→再追问" teaching pattern (AI_PROMPTS.md §6).
 * Shows RAG knowledge_hits when the backend surfaces them.
 */
import { useEffect, useRef, useState } from 'react'
import { Send, Trash2, StopCircle, BookOpen, Bot, User, Loader2, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { UseChatReturn } from '@/hooks/useChat'
import { cn } from '@/lib/utils'

interface ChatPanelProps {
  chat: UseChatReturn
  courseWeek: number
  weekTitle: string
  /** AI prompt template for this week's AI session (if any) */
  aiPromptTemplate?: string
}

/** Quick starters that map to common teaching tasks */
const QUICK_STARTS = [
  '请解释这个错误信息',
  '如何向量化这段代码？',
  '这个结果正确吗？如何验证？',
  '帮我理解这个数学概念',
  '推荐相关文献',
]

function MessageBubble({ turn }: { turn: UseChatReturn['turns'][number] }) {
  return (
    <div className="space-y-2 group">
      {/* User message */}
      <div className="flex items-start gap-2 justify-end">
        <div className="max-w-[85%] bg-violet-600/20 border border-violet-500/30 rounded-lg px-3 py-2">
          <p className="text-[12px] text-foreground whitespace-pre-wrap">{turn.userMessage}</p>
        </div>
        <div className="h-6 w-6 rounded-full bg-violet-600/40 flex items-center justify-center shrink-0 mt-0.5">
          <User className="h-3 w-3 text-violet-300" />
        </div>
      </div>

      {/* Assistant message */}
      <div className="flex items-start gap-2">
        <div className="h-6 w-6 rounded-full bg-emerald-800/40 flex items-center justify-center shrink-0 mt-0.5">
          <Bot className="h-3 w-3 text-emerald-400" />
        </div>
        <div className="flex-1 min-w-0">
          {turn.loading && (
            <div className="flex items-center gap-2 px-3 py-2 bg-muted/30 rounded-lg">
              <Loader2 className="h-3 w-3 text-emerald-400 animate-spin" />
              <span className="text-[11px] text-muted-foreground">思考中…</span>
            </div>
          )}
          {turn.error && (
            <div className="flex items-start gap-2 px-3 py-2 bg-destructive/10 border border-destructive/30 rounded-lg">
              <AlertTriangle className="h-3.5 w-3.5 text-destructive shrink-0 mt-0.5" />
              <p className="text-[11px] text-destructive">{turn.error}</p>
            </div>
          )}
          {turn.assistantMessage && (
            <div className="bg-muted/30 border border-border/60 rounded-lg px-3 py-2 space-y-1">
              <p className="text-[12px] text-foreground whitespace-pre-wrap leading-relaxed">
                {turn.assistantMessage}
              </p>
              {/* RAG knowledge hits */}
              {turn.knowledgeHits.length > 0 && (
                <div className="flex items-center gap-1 pt-1 flex-wrap border-t border-border/40 mt-1">
                  <BookOpen className="h-3 w-3 text-muted-foreground shrink-0" />
                  <span className="text-[10px] text-muted-foreground">课件命中：</span>
                  {turn.knowledgeHits.map((hit, i) => (
                    <Badge key={i} variant="muted" className="text-[9px] px-1 py-0 h-3.5">
                      {hit}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
          <p className="text-[10px] text-muted-foreground mt-0.5 pl-1">
            {turn.timestamp.toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  )
}

export function ChatPanel({ chat, courseWeek, weekTitle, aiPromptTemplate }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [showAiTemplate, setShowAiTemplate] = useState(false)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chat.turns])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || chat.loading) return
    setInput('')
    await chat.send(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleQuickStart = (qs: string) => {
    setInput(qs)
    textareaRef.current?.focus()
  }

  return (
    <div className="flex h-full flex-col bg-card border-l border-border">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-3 py-2 shrink-0">
        <div className="flex items-center gap-2">
          <Bot className="h-3.5 w-3.5 text-emerald-400" />
          <span className="text-xs font-semibold text-foreground tracking-wide uppercase">
            AI 教学助手
          </span>
          <Badge variant="muted" className="text-[10px]">
            第 {courseWeek} 周
          </Badge>
        </div>
        <div className="flex gap-1">
          {aiPromptTemplate && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-[10px] px-2 text-violet-400"
              onClick={() => setShowAiTemplate((v) => !v)}
            >
              AI 话术
            </Button>
          )}
          {chat.loading ? (
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={chat.cancel}>
              <StopCircle className="h-3 w-3 text-amber-400" />
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={chat.clear}
              disabled={chat.turns.length === 0}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* AI Prompt Template (for AI-session weeks) */}
      {showAiTemplate && aiPromptTemplate && (
        <div className="border-b border-border bg-violet-900/20 px-3 py-2 shrink-0">
          <div className="flex items-center gap-1.5 mb-1">
            <Bot className="h-3 w-3 text-violet-400" />
            <span className="text-[11px] font-medium text-violet-300">本周 AI 辅助环节</span>
          </div>
          <pre className="text-[10px] text-muted-foreground whitespace-pre-wrap font-sans leading-relaxed">
            {aiPromptTemplate}
          </pre>
          <Button
            variant="ghost"
            size="sm"
            className="mt-1 h-5 text-[10px] px-2 text-violet-400"
            onClick={() => {
              const lines = aiPromptTemplate.split('\n')
              const promptStart = lines.findIndex((l) => l.includes('建议提示词'))
              if (promptStart >= 0) {
                const block = lines
                  .slice(promptStart + 1)
                  .find((l) => l.includes('"'))
                const cleaned = block?.replace(/^["\s]+|["\s]+$/g, '') ?? ''
                if (cleaned) setInput(cleaned)
              }
              setShowAiTemplate(false)
            }}
          >
            使用建议提示词
          </Button>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 px-3 py-2">
        {chat.turns.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 gap-3">
            <div className="h-12 w-12 rounded-full bg-emerald-900/30 flex items-center justify-center">
              <Bot className="h-6 w-6 text-emerald-400" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-foreground">
                {weekTitle}
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                我是你的科学计算教学助手，有任何疑问都可以问我
              </p>
            </div>
            {/* Quick starts */}
            <div className="flex flex-wrap gap-1.5 justify-center max-w-xs">
              {QUICK_STARTS.map((qs) => (
                <button
                  key={qs}
                  onClick={() => handleQuickStart(qs)}
                  className="text-[10px] border border-border/60 rounded-full px-2.5 py-1 text-muted-foreground hover:text-foreground hover:border-violet-500/50 hover:bg-violet-900/20 transition-colors"
                >
                  {qs}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4 pb-2">
            {chat.turns.map((turn) => (
              <MessageBubble key={turn.id} turn={turn} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </ScrollArea>

      {/* Input area */}
      <div className="border-t border-border px-3 py-2 shrink-0">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`问关于第 ${courseWeek} 周的问题… (Enter 发送，Shift+Enter 换行)`}
            rows={2}
            className={cn(
              'flex-1 resize-none rounded-md border border-input bg-background px-3 py-2',
              'text-[12px] text-foreground placeholder:text-muted-foreground',
              'focus:outline-none focus:ring-1 focus:ring-ring',
              'min-h-[52px] max-h-32',
            )}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || chat.loading}
            size="icon"
            className="h-10 w-10 bg-emerald-700 hover:bg-emerald-600 text-white shrink-0"
          >
            {chat.loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
