import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { CheckCircle2, Loader2, XCircle } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { DiscordSettings } from '@/types/research'

interface DiscordPanelProps {
  value: DiscordSettings
  onChange: (value: DiscordSettings) => void
}

export function DiscordPanel({ value, onChange }: DiscordPanelProps) {
  const { register, handleSubmit } = useForm<DiscordSettings>({ defaultValues: value })
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  const onSubmit = handleSubmit(async (data) => {
    setStatus('loading')
    setMessage('')
    onChange(data)
    
    if (!data.bot_token || !data.channel_id) {
      setStatus('idle')
      return
    }

    try {
      const res = await fetch('http://localhost:8000/api/discord/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      const json = await res.json()
      
      if (!res.ok) {
        throw new Error(json.detail || 'Failed to verify Discord settings')
      }
      
      setStatus('success')
      setMessage(json.message)
    } catch (err: any) {
      setStatus('error')
      setMessage(err.message)
    }
  })

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Discord</p>
      </div>
      <Input placeholder="Discord Bot Token" type="password" autoComplete="off" {...register('bot_token')} />
      <Input placeholder="Channel ID" autoComplete="off" {...register('channel_id')} />
      <Input placeholder="Applicant Name (Optional)" autoComplete="off" {...register('applicant_name')} />
      <Input placeholder="Applicant Email (Optional)" type="email" autoComplete="off" {...register('applicant_email')} />
      
      {status === 'success' && (
        <div className="flex items-center gap-2 text-sm text-emerald-400">
          <CheckCircle2 className="h-4 w-4" />
          <span>{message}</span>
        </div>
      )}
      
      {status === 'error' && (
        <div className="flex items-start gap-2 text-sm text-red-400">
          <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      <Button type="submit" variant="secondary" className="w-full" disabled={status === 'loading'}>
        {status === 'loading' ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Verifying...
          </>
        ) : (
          'Save & Verify'
        )}
      </Button>
    </form>
  )
}
