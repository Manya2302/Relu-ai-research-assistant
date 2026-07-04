import { ExternalLink, Globe2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Competitor } from '@/types/research'

interface CompetitorGridProps {
  competitors: Competitor[]
}

export function CompetitorGrid({ competitors }: CompetitorGridProps) {
  if (!competitors.length) {
    return <p className="text-sm text-slate-500">No competitors identified.</p>
  }

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {competitors.map((competitor) => (
        <Card key={competitor.name} className="border-slate-800 bg-slate-950/70">
          <CardHeader className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-700 bg-slate-900 text-slate-300">
                <Globe2 className="h-5 w-5" />
              </div>
              <Badge>{competitor.website ? 'Official site' : 'Suggested rival'}</Badge>
            </div>
            <CardTitle className="text-base">{competitor.name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <a className="flex items-center gap-2 text-sm text-slate-300 transition hover:text-white" href={competitor.website || '#'} target="_blank" rel="noreferrer">
              {competitor.website || 'Website unavailable'}
              {competitor.website ? <ExternalLink className="h-3.5 w-3.5" /> : null}
            </a>
            <p className="text-sm leading-6 text-slate-400">{competitor.reason || 'Relevant competitor selected by the model.'}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
