import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, CircleAlert, Loader2 } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { ProgressEvent } from '@/types/research'

interface ResearchProgressProps {
  events: ProgressEvent[]
  progress: number
  error?: string
  isRunning: boolean
}

export function ResearchProgress({ events, progress, error, isRunning }: ResearchProgressProps) {
  const activeEvent = events[events.length - 1]

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4 shadow-glow">
      <div className="mb-3 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Research Progress</p>
          <p className="mt-1 text-sm text-slate-300">{error ? 'Research failed' : activeEvent?.message || 'Waiting...'}</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          {isRunning ? <Loader2 className="h-4 w-4 animate-spin text-slate-300" /> : <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
          {Math.min(Math.max(progress, 0), 100)}%
        </div>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-white via-slate-300 to-slate-500"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(Math.max(progress, 4), 100)}%` }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
        />
      </div>
      <div className="mt-4 grid gap-2">
        <AnimatePresence initial={false}>
          {events.slice(-6).map((event, index) => (
            <motion.div
              key={`${event.stage}-${index}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className={cn(
                'flex items-center gap-3 rounded-xl border px-3 py-2 text-sm',
                index === events.slice(-6).length - 1 ? 'border-slate-700 bg-slate-900/90 text-slate-100' : 'border-slate-800 bg-slate-950/40 text-slate-400',
              )}
            >
              {event.error ? <CircleAlert className="h-4 w-4 text-rose-400" /> : <span className="h-2.5 w-2.5 rounded-full bg-slate-500" />}
              <span>{event.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
