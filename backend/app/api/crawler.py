from __future__ import annotations

from fastapi import APIRouter

from app.services.crawler_service import WebsiteCrawler

router = APIRouter(prefix='/api', tags=['crawler'])


@router.post('/crawl')
async def crawl_website(payload: dict[str, str]):
    crawler = WebsiteCrawler()
    website_url = payload.get('website_url', '')
    pages = await crawler.crawl(website_url)
    return {'pages': [page.model_dump(mode='json') for page in pages]}