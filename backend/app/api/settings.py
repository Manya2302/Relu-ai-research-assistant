from __future__ import annotations

from fastapi import APIRouter

from app.settings import get_settings

router = APIRouter(prefix='/api', tags=['settings'])


@router.get('/settings')
async def app_settings():
    settings = get_settings()
    return {
        'app_name': settings.app_name,
        'app_version': settings.app_version,
        'api_prefix': settings.api_prefix,
        'groq_base_url': settings.groq_base_url,
        'serper_base_url': settings.serper_base_url,
    }