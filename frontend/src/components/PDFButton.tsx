import { Download } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { downloadPdf } from '@/services/api'

interface PDFButtonProps {
  pdfBase64: string
  filename: string
}

export function PDFButton({ pdfBase64, filename }: PDFButtonProps) {
  return (
    <Button type="button" variant="secondary" onClick={() => downloadPdf(pdfBase64, filename)}>
      <Download className="h-4 w-4" />
      Download PDF
    </Button>
  )
}
