import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'

import { ChatMessage } from '@/components/ChatMessage'
import { ResearchCard } from '@/components/ResearchCard'
import { ResearchInput } from '@/components/ResearchInput'
import { ResearchProgress } from '@/components/ResearchProgress'
import { Sidebar } from '@/components/Sidebar'
import { Button } from '@/components/ui/button'
import { loadStoredConfig, saveStoredConfig } from '@/services/storage'
import { useResearch } from '@/hooks/useResearch'
import type { ResearchRequest, StoredConfig } from '@/types/research'

export function Home() {
  const [config, setConfig] = useState<StoredConfig>(() => loadStoredConfig())
  const { events, result, isRunning, error, progress, run, reset } = useResearch()

  const messages = useMemo(() => {
    const intro = [
      'Enter a company name or website URL and I will locate the official site, crawl the important pages, analyze the data with Groq, and generate a PDF report.',
    ]
    return [
      ...intro.map((content) => ({ role: 'assistant' as const, content })),
      ...events
        .filter((event) => event.message)
        .map((event) => ({
          role: 'assistant' as const,
          content: event.error ? `Error: ${event.error}` : event.message,
        })),
      ...(result ? [{ role: 'assistant' as const, content: `Research complete for ${result.company_name || 'the requested company'}.` }] : []),
    ]
  }, [events, result])

  const handleSave = (nextConfig: StoredConfig) => {
    setConfig(nextConfig)
    saveStoredConfig(nextConfig)
  }

  const handleResearch = async (query: string) => {
    const payload: ResearchRequest = {
      query,
      input_type: /^https?:\/\//i.test(query) || /\.[a-z]{2,}\/?.*/i.test(query) ? 'website_url' : 'company_name',
      groq_api_key: config.groq_api_key,
      serper_api_key: config.serper_api_key,
      model: config.model,
      discord: config.discord,
    }
    await run(payload)
  }

  return (
    <div className="flex min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.09),_transparent_24%),linear-gradient(180deg,#020617_0%,#020617_38%,#000_100%)] text-slate-100">
      <Sidebar config={config} onSaveConfig={handleSave} />

      <main className="flex min-h-screen flex-1 flex-col overflow-hidden">
        <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/70 px-4 py-4 backdrop-blur-xl md:px-6">
          <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">Company Research Workspace</p>
              <h2 className="text-lg font-semibold text-slate-100">AI-powered company intelligence and automated reporting.</h2>
            </div>
            <div className="hidden items-center gap-2 md:flex">
              <Button type="button" variant="ghost" onClick={reset}>Reset</Button>
            </div>
          </div>
        </header>

        <section className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-5 px-4 py-6 md:px-6">
          {!result ? (
            <>
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="space-y-4">
                <ResearchProgress events={events} progress={progress} error={error} isRunning={isRunning} />
              </motion.div>

              <div className="space-y-4">
                {messages.map((message, index) => (
                  <motion.div key={`${message.role}-${index}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: index * 0.02 }}>
                    <ChatMessage role={message.role} content={message.content} />
                  </motion.div>
                ))}
              </div>
            </>
          ) : (
            <ResearchCard result={result} />
          )}
        </section>

        <ResearchInput isRunning={isRunning} onSubmit={handleResearch} />
      </main>
    </div>
  )
}
