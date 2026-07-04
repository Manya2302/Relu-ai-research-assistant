from __future__ import annotations

import json

import httpx

from app.settings import get_settings
from app.utils.helpers import safe_filename


class DiscordService:
    async def send_report(
        self,
        *,
        bot_token: str,
        channel_id: str,
        applicant_name: str,
        applicant_email: str,
        company_name: str,
        website: str,
        pdf_bytes: bytes,
        filename: str,
    ) -> bool:
        bot_token = bot_token.strip()
        channel_id = channel_id.strip()
        if not bot_token or not channel_id:
            return False

        message_content = (
            f'**Applicant Details**\n'
            f'Applicant Name: {applicant_name or "N/A"}\n'
            f'Applicant Email Address: {applicant_email or "N/A"}\n\n'
            f'**Research Details**\n'
            f'Company Name: {company_name or "N/A"}\n'
            f'Company Website: {website or "N/A"}'
        )
        payload = {'content': message_content}
        headers = {'Authorization': f'Bot {bot_token}'}
        base_url = get_settings().discord_api_base_url.rstrip('/')
        files = {'files[0]': (filename or safe_filename(company_name or 'report'), pdf_bytes, 'application/pdf')}

        async with httpx.AsyncClient(timeout=get_settings().request_timeout_seconds) as client:
            response = await client.post(
                f'{base_url}/channels/{channel_id}/messages',
                headers=headers,
                data={'payload_json': json.dumps(payload)},
                files=files,
            )
            if response.status_code >= 400:
                return False
        return True
