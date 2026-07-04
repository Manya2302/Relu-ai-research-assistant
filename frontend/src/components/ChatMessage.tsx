import { Bot, User2 } from 'lucide-react'

import { cn } from '@/lib/utils'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  return (
    <div className={cn('flex gap-3 rounded-2xl border p-4', role === 'user' ? 'border-slate-700 bg-slate-900/60' : 'border-slate-800 bg-slate-950/70')}>
      <div className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl', role === 'user' ? 'bg-white text-slate-950' : 'bg-slate-800 text-slate-100')}>
        {role === 'user' ? <User2 className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <p className="whitespace-pre-wrap text-sm leading-7 text-slate-200">{content}</p>
    </div>
  )
}
