from __future__ import annotations

from fastapi import APIRouter

from app.schemas.research import CompanyResearchResult, DiscordSettings
from app.services.discord_service import DiscordService
from app.services.pdf_service import PDFService

router = APIRouter(prefix='/api', tags=['discord'])
discord_service = DiscordService()
pdf_service = PDFService()


@router.post('/discord/send')
async def send_to_discord(payload: dict):
    discord = DiscordSettings(**payload['discord'])
    result = CompanyResearchResult(**payload['result'])
    pdf_bytes = pdf_service.build_pdf(result)
    sent = await discord_service.send_report(
        bot_token=discord.bot_token,
        channel_id=discord.channel_id,
        applicant_name=discord.applicant_name,
        applicant_email=discord.applicant_email,
        company_name=result.company_name,
        website=result.website,
        pdf_bytes=pdf_bytes,
        filename=result.report_filename,
    )
    return {'sent': sent}