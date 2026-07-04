from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

from app.api.crawler import router as crawler_router
from app.api.discord import router as discord_router
from app.api.pdf import router as pdf_router
from app.api.research import router as research_router
from app.api.settings import router as settings_router
from app.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(research_router)
app.include_router(crawler_router)
app.include_router(pdf_router)
app.include_router(discord_router)
app.include_router(settings_router)


@app.get('/health')
async def health():
    return {'status': 'ok', 'service': settings.app_name, 'version': settings.app_version}

# Serve React frontend for unified deployment
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'dist')
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        print(f"CATCH-ALL HIT: {request.method} {full_path}")
        # Allow API routes to pass through (though they shouldn't hit this due to routing order usually, but just in case)
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
            
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Fallback to index.html for React Router
        return FileResponse(os.path.join(frontend_dist, 'index.html'))
