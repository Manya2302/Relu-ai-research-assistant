import type { ReactNode } from 'react'

import { CalendarDays, Globe2, MapPinned, Phone, Building2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PDFButton } from '@/components/PDFButton'
import { CompetitorGrid } from '@/components/CompetitorGrid'
import type { CompanyResearchResult } from '@/types/research'

interface ResearchCardProps {
  result: CompanyResearchResult
}

export function ResearchCard({ result }: ResearchCardProps) {
  return (
    <Card className="overflow-hidden border-slate-800 bg-gradient-to-br from-slate-950 via-slate-950 to-slate-900/90">
      <div className="h-1 w-full bg-gradient-to-r from-white via-slate-400 to-slate-700" />
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <Badge className="w-fit">AI Research Complete</Badge>
            <CardTitle className="text-2xl md:text-3xl">{result.company_name || 'Unknown Company'}</CardTitle>
            <div className="flex flex-wrap gap-3 text-sm text-slate-400">
              {result.website ? (
                <a className="flex items-center gap-2 transition hover:text-white" href={result.website} target="_blank" rel="noreferrer">
                  <Globe2 className="h-4 w-4" />
                  {result.website}
                </a>
              ) : null}
              <span className="flex items-center gap-2"><CalendarDays className="h-4 w-4" /> {new Date(result.generated_at).toLocaleString()}</span>
            </div>
          </div>
          <div className="flex gap-3">
            <PDFButton pdfBase64={result.pdf_base64} filename={result.report_filename} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Metric label="Phone" value={result.phone || 'N/A'} icon={<Phone className="h-4 w-4" />} />
          <Metric label="Address" value={result.address || 'N/A'} icon={<MapPinned className="h-4 w-4" />} />
          <Metric label="Revenue" value={result.revenue || 'N/A'} icon={<Building2 className="h-4 w-4" />} />
          <Metric label="Industry" value={result.industry || 'N/A'} icon={<Building2 className="h-4 w-4" />} />
          <Metric label="Country" value={result.country || 'N/A'} icon={<Globe2 className="h-4 w-4" />} />
        </section>

        <section className="space-y-3 rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">Company Summary</h3>
          <p className="text-sm leading-7 text-slate-300">{result.summary || 'No summary available.'}</p>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <ListBlock title="Products / Services" items={result.products} emptyText="No products identified." />
          <ListBlock title="Pain Points" items={result.pain_points} emptyText="No pain points identified." />
        </section>

        <section className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">Competitors</h3>
          <CompetitorGrid competitors={result.competitors} />
        </section>

        {result.sources?.length ? (
          <section className="space-y-3 rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">Research Sources</h3>
            <div className="flex flex-wrap gap-2">
              {result.sources.slice(0, 12).map((source) => (
                <Badge key={source.url} className="max-w-full truncate" title={source.url}>
                  {source.title || source.url}
                </Badge>
              ))}
            </div>
          </section>
        ) : null}
      </CardContent>
    </Card>
  )
}

function Metric({ label, value, icon }: { label: string; value: string; icon: ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-500">
        {icon}
        {label}
      </div>
      <p className="mt-3 break-words text-sm leading-6 text-slate-200">{value}</p>
    </div>
  )
}

function ListBlock({ title, items, emptyText }: { title: string; items: string[]; emptyText: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
      <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">{title}</h3>
      <div className="mt-4 flex flex-wrap gap-2">
        {items.length ? items.map((item) => <Badge key={item}>{item}</Badge>) : <p className="text-sm text-slate-500">{emptyText}</p>}
      </div>
    </div>
  )
}
