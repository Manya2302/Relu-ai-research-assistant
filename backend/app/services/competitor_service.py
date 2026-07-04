from __future__ import annotations

from app.config import COMPETITOR_LIMIT
from app.schemas.research import Competitor, ResearchSource
from app.services.serper_service import SerperService
from app.utils.cleaner import dedupe_preserve_order, normalize_whitespace
from app.utils.helpers import normalize_url


class CompetitorService:
    def __init__(self, serper_service: SerperService) -> None:
        self.serper_service = serper_service

    async def enrich_competitors(self, company_name: str, competitors: list[Competitor], industry: str, country: str, products: list[str]) -> list[Competitor]:
        enriched = list(competitors)
        for competitor in enriched:
            if competitor.website:
                competitor.website = normalize_url(competitor.website)

        missing = [competitor for competitor in enriched if not competitor.website]
        for competitor in missing:
            competitor.website = await self._find_official_site(competitor.name)

        if len(enriched) < COMPETITOR_LIMIT:
            discovered = await self._discover_candidates(company_name, industry, country, products)
            for competitor in discovered:
                if len(enriched) >= COMPETITOR_LIMIT:
                    break
                if competitor.name.lower() not in {item.name.lower() for item in enriched}:
                    enriched.append(competitor)

        return enriched[:COMPETITOR_LIMIT]

    async def _find_official_site(self, name: str) -> str:
        try:
            return await self.serper_service.find_official_website(name)
        except Exception:
            return ''

    async def _discover_candidates(self, company_name: str, industry: str, country: str, products: list[str]) -> list[Competitor]:
        sources = await self.serper_service.find_competitor_sources(company_name, industry, country, products)
        competitors: list[Competitor] = []
        for source in sources:
            name = self._guess_competitor_name(source)
            if not name:
                continue
            website = normalize_url(source.url)
            reason = normalize_whitespace(source.snippet or 'Relevant company in the same market segment.')
            competitors.append(Competitor(name=name, website=website, reason=reason))
        deduped = []
        seen: set[str] = set()
        for competitor in competitors:
            key = competitor.name.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(competitor)
        return deduped[:COMPETITOR_LIMIT]

    def _guess_competitor_name(self, source: ResearchSource) -> str:
        title = normalize_whitespace(source.title)
        if not title:
            return ''
        for separator in (' - ', ' | ', ' / '):
            if separator in title:
                title = title.split(separator, 1)[0]
                break
        return title[:120]
