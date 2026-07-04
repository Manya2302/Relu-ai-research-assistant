import { useEffect } from 'react'

import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, ChevronDown, Loader2, XCircle } from 'lucide-react'

import { listGroqModels } from '@/services/api'

interface ModelSelectorProps {
  groqApiKey: string
  value: string
  onChange: (value: string) => void
  onStatusChange?: (status: 'idle' | 'loading' | 'verified' | 'error', message: string) => void
}

export function ModelSelector({ groqApiKey, value, onChange, onStatusChange }: ModelSelectorProps) {
  const modelsQuery = useQuery({
    queryKey: ['groq-models', groqApiKey],
    queryFn: () => listGroqModels(groqApiKey),
    enabled: Boolean(groqApiKey.trim()),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (!value && modelsQuery.data?.length) {
      onChange(modelsQuery.data[0].id)
    }
  }, [modelsQuery.data, onChange, value])

  useEffect(() => {
    if (!onStatusChange) {
      return
    }
    if (!groqApiKey.trim()) {
      onStatusChange('idle', 'Enter an API key (Groq, OpenRouter, OpenAI, Gemini) to verify it.')
      return
    }
    if (modelsQuery.isFetching) {
      onStatusChange('loading', 'Verifying API key...')
      return
    }
    if (modelsQuery.isError) {
      onStatusChange('error', 'API key verification failed.')
      return
    }
    const detectProvider = (key: string) => {
      const k = key.trim()
      if (k.startsWith('gsk_')) return 'Groq'
      if (k.startsWith('sk-or-')) return 'OpenRouter'
      if (k.startsWith('sk-proj-') || (k.startsWith('sk-') && !k.startsWith('sk-ant-'))) return 'OpenAI'
      if (k.startsWith('AIza')) return 'Gemini'
      if (k.startsWith('sk-ant-')) return 'Anthropic'
      return 'API'
    }

    if (modelsQuery.isSuccess) {
      const provider = detectProvider(groqApiKey)
      onStatusChange('verified', `${provider} key verified. ${modelsQuery.data?.length ?? 0} models available.`)
    }
  }, [groqApiKey, modelsQuery.data?.length, modelsQuery.isError, modelsQuery.isFetching, modelsQuery.isSuccess, onStatusChange])

  const modelOptions = modelsQuery.data ?? []

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400">AI Model</label>
        {modelsQuery.isFetching ? <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-500" /> : null}
      </div>
      <div className="relative">
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="h-11 w-full appearance-none rounded-xl border border-slate-700 bg-slate-900/80 px-4 pr-10 text-sm text-slate-100 outline-none transition focus:ring-2 focus:ring-slate-500"
        >
          {!modelOptions.length ? <option value={value || 'llama-3.1-70b-versatile'}>{value || 'llama-3.1-70b-versatile'}</option> : null}
          {modelOptions.map((model) => (
            <option key={model.id} value={model.id}>
              {model.label || model.id}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
      </div>
      {modelsQuery.isError ? <p className="text-xs text-rose-300">Enter a valid API key to load live model options. The default model remains available.</p> : null}
      {!groqApiKey.trim() ? (
        <p className="text-xs text-slate-500">Save your API key to populate the dropdown dynamically.</p>
      ) : null}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        {modelsQuery.isFetching ? <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-400" /> : null}
        {modelsQuery.isSuccess ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> : null}
        {modelsQuery.isError ? <XCircle className="h-3.5 w-3.5 text-rose-400" /> : null}
        <span>{modelsQuery.isSuccess ? 'API key is working' : modelsQuery.isError ? 'API key verification failed' : groqApiKey.trim() ? 'Checking API key...' : 'API key not entered'}</span>
      </div>
    </div>
  )
}
