from __future__ import annotations

import base64
import logging
from typing import Awaitable, Callable

from app.schemas.research import CompanyResearchContext, CompanyResearchResult, DiscordSettings, ResearchRequest, ResearchSource
from app.services.cache import session_cache
from app.services.company_parser import CompanyParser
from app.services.competitor_service import CompetitorService
from app.services.crawler_service import WebsiteCrawler
from app.services.discord_service import DiscordService
from app.services.openrouter_service import GroqService
from app.services.pdf_service import PDFService
from app.services.serper_service import SerperService
from app.settings import get_settings
from app.utils.cleaner import extract_phone_numbers, normalize_whitespace
from app.utils.helpers import guess_company_name_from_url, is_company_name_query, normalize_url, stable_hash

logger = logging.getLogger(__name__)
ProgressCallback = Callable[[str, str, int], Awaitable[None]]
REPORT_VERSION = '17-page-intelligence-report-v3'


class ResearchOrchestrator:
    def __init__(self) -> None:
        self.parser = CompanyParser()
        self.pdf_service = PDFService()
        self.discord_service = DiscordService()

    async def run(self, request: ResearchRequest, progress: ProgressCallback | None = None) -> CompanyResearchResult:
        cache_payload = request.model_dump(exclude={'groq_api_key', 'serper_api_key', 'discord'})
        cache_payload['report_version'] = REPORT_VERSION
        cache_key = stable_hash(cache_payload)
        cached = await session_cache.get(cache_key)
        if cached:
            if progress:
                await progress('cache', 'Loaded report from session cache.', 100)
            return cached

        serper = SerperService(request.serper_api_key)
        groq = GroqService(request.groq_api_key)
        competitor_service = CompetitorService(serper)

        await self._emit(progress, 'searching', 'Searching company...', 10)
        website = normalize_url(request.query) if request.input_type == 'website_url' else ''
        if not website:
            website = await serper.find_official_website(request.query)
        if not website:
            raise ValueError('Company not found. Please try a different company name or website URL.')

        await self._emit(progress, 'crawling', 'Crawling website...', 35)
        crawler = WebsiteCrawler()
        pages = await crawler.crawl(website)
        if not pages:
            logger.warning('Crawler returned no extractable pages for %s; continuing with public sources.', website)

        company_name = request.query if is_company_name_query(request.query) else guess_company_name_from_url(website)
        search_seed = company_name or website
        public_sources = await serper.search_public_sources(search_seed, website)
        search_sources = await serper.find_competitor_sources(search_seed, '', '', [])
        context = self.parser.build_context(request.query, website, search_sources, public_sources, pages)

        await self._emit(progress, 'analyzing', 'Analyzing with Your AI...', 70)
        result = await groq.generate_research(request.model, context)
        result.website = result.website or website
        result.company_name = result.company_name or context.company_name
        result.phone = result.phone or self._first_phone_value(context, pages, public_sources, search_sources)
        result.address = result.address or self._first_address_value(context, pages, public_sources, search_sources)
        result.industry = result.industry or context.inferred_industry
        result.country = result.country or context.inferred_country
        result.sources = public_sources[:8]
        result.references = self._build_references(website, pages, public_sources, search_sources)
        result.knowledge_graph = context.knowledge_graph
        result.crawler_pages = pages
        result.crawler_stats = self._build_crawler_stats(website, pages, search_sources, public_sources)
        result.competitors = await competitor_service.enrich_competitors(
            result.company_name,
            result.competitors,
            result.industry,
            result.country,
            result.products,
        )

        await self._emit(progress, 'pdf', 'Generating PDF...', 88)
        pdf_bytes = self.pdf_service.build_pdf(result)
        result.pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        result.report_filename = self.pdf_service.filename_for(result)

        if request.discord and request.discord.bot_token and request.discord.channel_id:
            await self._send_to_discord(request.discord, result, pdf_bytes)

        await session_cache.set(cache_key, result, ttl_seconds=900)
        await self._emit(progress, 'complete', 'Complete', 100)
        return result

    async def _send_to_discord(self, discord: DiscordSettings, result: CompanyResearchResult, pdf_bytes: bytes) -> None:
        try:
            await self.discord_service.send_report(
                bot_token=discord.bot_token,
                channel_id=discord.channel_id,
                applicant_name=discord.applicant_name,
                applicant_email=discord.applicant_email,
                company_name=result.company_name,
                website=result.website,
                pdf_bytes=pdf_bytes,
                filename=result.report_filename,
            )
        except Exception as exc:
            logger.warning('Discord notification failed: %s', exc)

    async def _emit(self, progress: ProgressCallback | None, stage: str, message: str, percent: int) -> None:
        if progress:
            await progress(stage, message, percent)

    def _build_references(self, website: str, pages, public_sources, search_sources) -> list[ResearchSource]:
        references: list[ResearchSource] = []
        references.append(ResearchSource(title='Official Website', url=website, snippet='Primary company domain'))
        references.extend(public_sources[:12])
        references.extend(search_sources[:8])
        seen: set[str] = set()
        deduped: list[ResearchSource] = []
        for source in references:
            key = source.url.lower().strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(source)
        return deduped[:20]

    def _build_crawler_stats(self, website: str, pages, search_sources, public_sources) -> dict[str, int]:
        internal_links = len({page.url for page in pages})
        external_links = len({source.url for source in public_sources + search_sources if source.url and not source.url.startswith(website)})
        docs = len([page for page in pages if any(page.url.lower().endswith(ext) for ext in ('.pdf', '.doc', '.docx', '.ppt', '.pptx'))])
        images = len([page for page in pages if any(page.url.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'))])
        videos = len([page for page in pages if any(page.url.lower().endswith(ext) for ext in ('.mp4', '.mov', '.webm', '.avi'))])
        return {
            'pages_crawled': len(pages),
            'total_urls': len(pages) + len(public_sources) + len(search_sources),
            'internal_links': internal_links,
            'external_links': external_links,
            'documents': docs,
            'images': images,
            'videos': videos,
            'sources_used': len(public_sources) + len(search_sources) + 1,
            'extraction_time_seconds': 0,
            'ai_tokens_estimate': len((getattr(pages[0], 'text', '') if pages else '') or '') // 4,
        }

    def _first_structured_value(self, context, key: str) -> str:
        values = context.structured_text.get(key, []) if getattr(context, 'structured_text', None) else []
        for value in values:
            text = str(value).strip()
            if text:
                return text
        return ''

    def _first_page_value(self, pages, attr: str) -> str:
        for page in pages or []:
            values = getattr(page, attr, []) or []
            for value in values:
                text = str(value).strip()
                if text:
                    return text
        return ''

    def _first_phone_value(self, context, pages, public_sources, search_sources) -> str:
        candidates: list[str] = []
        candidates.extend(context.structured_text.get('phones', []) if getattr(context, 'structured_text', None) else [])
        for page in pages or []:
            candidates.extend(page.phone_numbers or [])
            candidates.extend(extract_phone_numbers(page.text or ''))
            candidates.extend(extract_phone_numbers(' '.join(page.headings or [])))
            candidates.extend(extract_phone_numbers(' '.join(page.paragraphs or [])))
        for source in list(public_sources or []) + list(search_sources or []):
            candidates.extend(extract_phone_numbers(' '.join([source.title or '', source.snippet or '', source.url or ''])))
        return self._dedupe_contact_value(candidates)

    def _first_address_value(self, context, pages, public_sources, search_sources) -> str:
        candidates: list[str] = []
        candidates.extend(context.structured_text.get('addresses', []) if getattr(context, 'structured_text', None) else [])
        for page in pages or []:
            candidates.extend(page.addresses or [])
            candidates.extend(self._extract_address_like_text(page.text or ''))
            candidates.extend(self._extract_address_like_text(' '.join(page.headings or [])))
            candidates.extend(self._extract_address_like_text(' '.join(page.paragraphs or [])))
        for source in list(public_sources or []) + list(search_sources or []):
            candidates.extend(self._extract_address_like_text(' '.join([source.title or '', source.snippet or '', source.url or ''])))
            
        candidates = [c for c in candidates if 'login' not in c.lower() and 'register' not in c.lower() and len(c) > 10 and any(char.isdigit() for char in c)]
        return self._dedupe_contact_value(candidates)

    def _extract_address_like_text(self, text: str) -> list[str]:
        if not text:
            return []
        chunks: list[str] = []
        for piece in text.replace('|', '\n').split('\n'):
            value = normalize_whitespace(piece)
            lowered = value.lower()
            if len(value) >= 12 and any(token in lowered for token in ('address', 'headquarters', 'hq', 'campus', 'office', 'location')):
                chunks.append(value)
        return chunks

    def _dedupe_contact_value(self, candidates: list[str]) -> str:
        seen: set[str] = set()
        for candidate in candidates:
            value = normalize_whitespace(str(candidate))
            if not value:
                continue
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            return value
        return ''
