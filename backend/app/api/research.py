from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.schemas.research import ModelListRequest, ProgressEvent, ResearchRequest, DiscordSettings
from app.services.research_orchestrator import ResearchOrchestrator
from app.services.openrouter_service import GroqService

router = APIRouter(prefix='/api', tags=['research'])
orchestrator = ResearchOrchestrator()


@router.post('/models')
async def list_models(request: ModelListRequest):
    service = GroqService(request.groq_api_key)
    try:
        models = await service.list_models()
        return {'models': [model.model_dump(mode='json') for model in models]}
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})


@router.post('/discord/verify')
async def verify_discord(request: DiscordSettings):
    import httpx
    from app.settings import get_settings
    if not request.bot_token or not request.channel_id:
        return JSONResponse(status_code=400, content={"detail": "Missing bot token or channel ID"})
    
    headers = {'Authorization': f'Bot {request.bot_token.strip()}'}
    base_url = get_settings().discord_api_base_url.rstrip('/')
    
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(
            f'{base_url}/channels/{request.channel_id.strip()}',
            headers=headers,
        )
        if response.status_code == 200:
            return {"status": "ok", "message": "Verified! Bot has access to this channel."}
        elif response.status_code == 401:
            return JSONResponse(status_code=401, content={"detail": "Invalid bot token."})
        elif response.status_code == 404:
            return JSONResponse(status_code=404, content={"detail": "Channel not found. Check the ID."})
        elif response.status_code == 403:
            return JSONResponse(status_code=403, content={"detail": "Bot doesn't have permissions to view this channel."})
        else:
            return JSONResponse(status_code=response.status_code, content={"detail": f"Discord API error: {response.status_code}"})

@router.post('/research')
async def research_company(request: ResearchRequest):
    result = await orchestrator.run(request)
    return JSONResponse(content=result.model_dump(mode='json'))


@router.websocket('/ws/research')
async def research_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        request = ResearchRequest(**payload)

        async def emit(stage: str, message: str, progress: int) -> None:
            await websocket.send_json(ProgressEvent(stage=stage, message=message, progress=progress).model_dump(mode='json'))

        result = await orchestrator.run(request, progress=emit)
        await websocket.send_json(ProgressEvent(stage='complete', message='Complete', progress=100, done=True, result=result).model_dump(mode='json'))
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await websocket.send_json(ProgressEvent(stage='error', message='Research failed', progress=0, done=True, error=str(exc)).model_dump(mode='json'))
        await websocket.close()
