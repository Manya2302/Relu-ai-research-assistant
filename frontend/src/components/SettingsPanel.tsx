import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ModelSelector } from '@/components/ModelSelector'
import type { DiscordSettings, StoredConfig } from '@/types/research'

type VerificationStatus = 'idle' | 'loading' | 'verified' | 'error'

interface SettingsPanelProps {
  value: StoredConfig
  onSave: (value: StoredConfig) => void
}

export function SettingsPanel({ value, onSave }: SettingsPanelProps) {
  const { register, handleSubmit, watch, reset, setValue } = useForm<StoredConfig>({ defaultValues: value })
  const groqApiKey = watch('groq_api_key')
  const model = watch('model')
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus>('idle')
  const [verificationMessage, setVerificationMessage] = useState('Enter an API key to verify it.')

  useEffect(() => {
    reset(value)
  }, [reset, value])

  useEffect(() => {
    if (!groqApiKey.trim()) {
      setVerificationStatus('idle')
      setVerificationMessage('Enter an API key to verify it.')
    }
  }, [groqApiKey])

  const submit = handleSubmit((data) => {
    onSave(data)
  })

  return (
    <form onSubmit={submit} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
      <div>
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Research Settings</p>
          <span
            className={[
              'inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-[11px] font-medium',
              verificationStatus === 'verified'
                ? 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                : verificationStatus === 'error'
                  ? 'border border-rose-500/30 bg-rose-500/10 text-rose-300'
                  : 'border border-slate-700 bg-slate-900/80 text-slate-400',
            ].join(' ')}
          >
            <span
              className={[
                'h-2 w-2 rounded-full',
                verificationStatus === 'verified'
                  ? 'bg-emerald-400'
                  : verificationStatus === 'error'
                    ? 'bg-rose-400'
                    : verificationStatus === 'loading'
                      ? 'bg-amber-400'
                      : 'bg-slate-500',
              ].join(' ')}
            />
            {verificationStatus === 'verified' ? 'API key verified' : verificationStatus === 'error' ? 'API key invalid' : verificationStatus === 'loading' ? 'Verifying key' : 'API key not verified'}
          </span>
        </div>
        <p className="mt-1 text-sm text-slate-500">Store your API keys locally and send them to the backend only when you research.</p>
      </div>
      <Input placeholder="LLM API Key (Groq, Gemini, OpenRouter, etc.)" type="password" autoComplete="off" {...register('groq_api_key')} />
      <Input placeholder="Serper API Key" type="password" autoComplete="off" {...register('serper_api_key')} />
      <ModelSelector
        groqApiKey={groqApiKey}
        value={model}
        onChange={(nextValue) => setValue('model', nextValue, { shouldDirty: true })}
        onStatusChange={(status, message) => {
          setVerificationStatus(status)
          setVerificationMessage(message)
        }}
      />
      <p className={verificationStatus === 'verified' ? 'text-xs text-emerald-300' : verificationStatus === 'error' ? 'text-xs text-rose-300' : 'text-xs text-slate-500'}>{verificationMessage}</p>
      <Button type="submit" className="w-full">
        Save Configuration
      </Button>
    </form>
  )
}

export function sanitizeDiscordSettings(value: StoredConfig): DiscordSettings {
  return {
    bot_token: value.discord.bot_token,
    channel_id: value.discord.channel_id,
    applicant_name: value.discord.applicant_name,
    applicant_email: value.discord.applicant_email,
  }
}
