from __future__ import annotations

from fastapi import APIRouter, Response

from app.schemas.research import CompanyResearchResult
from app.services.pdf_service import PDFService

router = APIRouter(prefix='/api', tags=['pdf'])
pdf_service = PDFService()


@router.post('/pdf')
async def generate_pdf(result: CompanyResearchResult):
    pdf_bytes = pdf_service.build_pdf(result)
    filename = pdf_service.filename_for(result)
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )