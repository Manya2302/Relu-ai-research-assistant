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

  useEffect(() => {
    setFocus('query')
  }, [setFocus])

  const submit = handleSubmit(async (values) => {
    await onSubmit(values.query)
    reset({ query: '' })
  })

  return (
    <form onSubmit={submit} className="sticky bottom-0 z-20 border-t border-slate-800 bg-gradient-to-t from-slate-950 via-slate-950/95 to-transparent p-4 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-4xl items-center gap-3 rounded-2xl border border-slate-700 bg-slate-900/90 px-4 py-3 shadow-glow">
        <Search className="h-4 w-4 shrink-0 text-slate-500" />
        <Input
          className="border-none bg-transparent px-0 text-base placeholder:text-slate-500 focus:ring-0"
          placeholder="Enter a company name or website URL"
          autoComplete="off"
          {...register('query')}
        />
        <Button type="submit" size="lg" disabled={isRunning} className="shrink-0">
          {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
          Research
        </Button>
      </div>
    </form>
  )
}
