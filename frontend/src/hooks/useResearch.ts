import { useCallback, useMemo, useState } from 'react'

import { runResearchStream } from '@/services/api'
import type { CompanyResearchResult, ProgressEvent, ResearchRequest } from '@/types/research'

const INITIAL_EVENTS: ProgressEvent[] = [
  { stage: 'idle', message: 'Ready to research.', progress: 0 },
]

export function useResearch() {
  const [events, setEvents] = useState<ProgressEvent[]>(INITIAL_EVENTS)
  const [result, setResult] = useState<CompanyResearchResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState('')

  const progress = useMemo(() => events.at(-1)?.progress ?? 0, [events])

  const run = useCallback(async (request: ResearchRequest) => {
    setIsRunning(true)
    setError('')
    setResult(null)
    setEvents([{ stage: 'queued', message: 'Preparing research request...', progress: 2 }])

    try {
      const finalEvent = await runResearchStream(request, (event) => {
        setEvents((current: ProgressEvent[]) => [...current, event])
        if (event.result) {
          setResult(event.result)
        }
      })
      if (finalEvent.result) {
        setResult(finalEvent.result)
      }
      return finalEvent.result ?? null
    } catch (thrown) {
      const message = thrown instanceof Error ? thrown.message : 'Unable to complete research.'
      setError(message)
      throw thrown
    } finally {
      setIsRunning(false)
    }
  }, [])

  const reset = useCallback(() => {
    setEvents(INITIAL_EVENTS)
    setResult(null)
    setError('')
    setIsRunning(false)
  }, [])

  return {
    events,
    result,
    isRunning,
    error,
    progress,
    run,
    reset,
  }
}
