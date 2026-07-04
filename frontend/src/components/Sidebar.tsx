import { BrainCircuit, Building2, ShieldCheck, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { DiscordPanel } from '@/components/DiscordPanel'
import { SettingsPanel } from '@/components/SettingsPanel'
import type { StoredConfig } from '@/types/research'

interface SidebarProps {
  config: StoredConfig
  onSaveConfig: (value: StoredConfig) => void
  isMobileOpen?: boolean
  onCloseMobile?: () => void
}

export function Sidebar({ config, onSaveConfig, isMobileOpen, onCloseMobile }: SidebarProps) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm md:hidden" onClick={onCloseMobile} />
      )}
      
      <aside className={`fixed inset-y-0 left-0 z-50 flex h-full w-[85vw] max-w-[360px] flex-col gap-4 overflow-y-auto border-r border-slate-800 bg-slate-950/95 p-4 backdrop-blur-xl transition-transform duration-300 ease-in-out md:static md:w-[360px] md:min-w-[360px] md:translate-x-0 ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between md:hidden mb-2">
          <h2 className="text-sm font-semibold text-slate-100 uppercase tracking-widest">Settings</h2>
          <Button variant="ghost" size="icon" onClick={onCloseMobile}>
            <X className="h-5 w-5" />
          </Button>
        </div>
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-4 shadow-glow">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-slate-950 shadow-md">
            <BrainCircuit className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-100">AI Company Research Assistant</h1>
            <p className="text-sm text-slate-400">Relu Consultancy Hiring Challenge</p>
          </div>
        </div>
        <div className="mt-4 grid gap-2 text-xs text-slate-400">
          <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2"><Building2 className="h-4 w-4" /> Serper search + website crawling</div>
          <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2"><ShieldCheck className="h-4 w-4" /> Groq model selection + PDF export</div>
        </div>
      </div>

      <SettingsPanel value={config} onSave={onSaveConfig} />
      <DiscordPanel value={config.discord} onChange={(discord) => onSaveConfig({ ...config, discord })} />


      <div className="mt-auto hidden md:block">
      </div>
    </aside>
    </>
  )
}
