import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { ArrowRight, Loader2, Search } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface ResearchInputProps {
  isRunning: boolean
  onSubmit: (value: string) => Promise<void> | void
}

interface FormValues {
  query: string
}

export function ResearchInput({ isRunning, onSubmit }: ResearchInputProps) {
  const { register, handleSubmit, reset, setFocus } = useForm<FormValues>({ defaultValues: { query: '' } })

  // Removed auto-focus to prevent page scrolling to bottom on load

  const submit = handleSubmit(async (values) => {
    await onSubmit(values.query)
    reset({ query: '' })
  })

  return (
    <form onSubmit={submit} className="sticky bottom-0 z-20 border-t border-slate-800 bg-gradient-to-t from-slate-950 via-slate-950/95 to-transparent p-4 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-3xl items-center gap-3 rounded-2xl border border-slate-800 bg-[#0a0a0a] px-3 py-2.5 shadow-xl">
        <Input
          className="border-none bg-transparent px-3 text-base text-slate-100 placeholder:text-slate-500 focus-visible:ring-0 focus:ring-0"
          placeholder="Enter a company name (e.g., Apple, linear.app)"
          autoComplete="off"
          {...register('query')}
        />
        <Button type="submit" size="default" disabled={isRunning} className="shrink-0 bg-amber-600 hover:bg-amber-700 text-white font-medium rounded-xl px-5 h-10">
          {isRunning ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          Research {isRunning ? '' : '→'}
        </Button>
      </div>
    </form>
  )
}
