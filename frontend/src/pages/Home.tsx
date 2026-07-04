import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Menu } from 'lucide-react'

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
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const { events, result, isRunning, error, progress, run, reset } = useResearch()

  const messages = useMemo(() => {
    return [
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
    <div className="flex h-[100dvh] w-full overflow-hidden bg-[#050505] text-slate-100 font-sans selection:bg-amber-500/30">
      <Sidebar
        config={config}
        onSaveConfig={handleSave}
        isMobileOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      <main className="flex h-full flex-1 flex-col overflow-hidden relative">
        <header className="sticky top-0 z-20 border-b border-white/5 bg-[#050505]/80 px-4 py-4 backdrop-blur-xl md:px-6">
          <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Button type="button" variant="ghost" size="icon" className="md:hidden text-slate-400 hover:text-white" onClick={() => setIsMobileSidebarOpen(true)}>
                <Menu className="h-6 w-6" />
              </Button>
              <h1 className="text-xl font-bold text-white flex items-center gap-3">
                Company Research
                <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-500 border border-emerald-500/20">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                  Live
                </span>
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <Button type="button" variant="ghost" onClick={reset} className="hidden md:flex text-slate-400 hover:text-white">Reset</Button>
            </div>
          </div>
        </header>

        <section className="mx-auto flex w-full max-w-5xl flex-1 flex-col overflow-y-auto overflow-x-hidden px-4 py-6 md:px-6">
          {!result && events.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center text-center mt-10 md:mt-20">
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
                <span className="text-amber-500/90 text-[11px] font-bold tracking-[0.25em] uppercase mb-6 block">
                  AI-Powered Intelligence
                </span>
                <h2 className="text-[2.75rem] md:text-7xl font-bold tracking-tight text-white mb-6 leading-[1.05] max-w-2xl mx-auto">
                  Know any<br />company<br />in minutes.
                </h2>
                <p className="text-slate-400 max-w-lg mx-auto mb-10 text-base md:text-lg leading-relaxed">
                  Enter a company name or website URL to get AI-powered insights, competitor analysis, pain points, and a professional PDF report.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-3 mb-16">
                  {['notion.so', 'Figma', 'Linear', 'Vercel'].map((term) => (
                    <button
                      key={term}
                      onClick={() => handleResearch(term)}
                      className="px-5 py-2 rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-slate-300 text-sm hover:bg-[#222] hover:text-white transition-colors font-medium"
                    >
                      {term}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-4 text-[11px] text-slate-500 w-full max-w-xs mx-auto">
                  <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent to-slate-800"></div>
                  <span className="tracking-wide">Configure API keys in the sidebar to get started</span>
                  <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent to-slate-800"></div>
                </div>
              </motion.div>
            </div>
          ) : !result ? (
            <div className="flex flex-col gap-5 w-full max-w-3xl mx-auto">
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
            </div>
          ) : (
            <ResearchCard result={result} />
          )}
        </section>

        <ResearchInput isRunning={isRunning} onSubmit={handleResearch} />
      </main>
    </div>
  )
}
