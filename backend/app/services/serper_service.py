from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import MODEL_LIMIT
from app.schemas.research import ResearchSource
from app.settings import get_settings
from app.utils.cleaner import dedupe_preserve_order, normalize_whitespace
from app.utils.helpers import domain_from_url, is_valid_research_url, normalize_url

logger = logging.getLogger(__name__)

EXCLUDED_HOSTS = {
    'linkedin.com',
    'facebook.com',
    'instagram.com',
    'youtube.com',
    'x.com',
    'twitter.com',
    'crunchbase.com',
    'wikipedia.org',
    'bloomberg.com',
    'zoominfo.com',
    'rocketreach.co',
    'signalhire.com',
    'mapquest.com',
}


@dataclass(slots=True)
class SearchResult:
    title: str
    link: str
    snippet: str


class SerperService:
    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key.strip()
        self.base_url = (base_url or settings.serper_base_url).rstrip('/')
        self.timeout = settings.request_timeout_seconds

    async def search(self, query: str, num: int = 10) -> list[SearchResult]:
        if not self.api_key:
            raise ValueError('Serper API key is required.')
        payload = {'q': query, 'num': min(max(num, 1), 10)}
        headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f'{self.base_url}/search', json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return self._parse_results(data)

    async def search_public_sources(self, company_name: str, website: str | None = None) -> list[ResearchSource]:
        queries = self._build_discovery_queries(company_name, website)
        results: list[ResearchSource] = []
        for query in queries:
            try:
                search_results = await self.search(query, num=5)
                for item in search_results:
                    results.append(
                        ResearchSource(
                            title=item.title,
                            url=item.link,
                            snippet=item.snippet,
                        )
                    )
            except Exception as exc:  # pragma: no cover - surfaced in UI
                logger.warning('Serper search failed for %s: %s', query, exc)
        return self._dedupe_sources(results)[:MODEL_LIMIT]

    async def find_official_website(self, company_name: str) -> str:
        results = await self.search(f'{company_name} official website', num=10)
        company_domain_tokens = self._domain_tokens(company_name)
        for item in results:
            if self._looks_official(item.link, company_domain_tokens):
                return normalize_url(item.link)
        for item in results:
            if item.link and is_valid_research_url(item.link):
                return normalize_url(item.link)
        return ''

    async def find_competitor_sources(self, company_name: str, industry: str = '', country: str = '', products: list[str] | None = None) -> list[ResearchSource]:
        parts = [company_name, industry, country, 'competitors']
        if products:
            parts.extend(products[:3])
        query = ' '.join(part for part in parts if part).strip()
        results = await self.search(query, num=10)
        return [ResearchSource(title=item.title, url=item.link, snippet=item.snippet) for item in results]

    def _build_discovery_queries(self, company_name: str, website: str | None) -> list[str]:
        queries = [
            f'{company_name} official website',
            f'{company_name} investor relations',
            f'{company_name} annual report',
            f'{company_name} financial results',
            f'{company_name} annual revenue',
            f'{company_name} products',
            f'{company_name} services',
            f'{company_name} pricing',
            f'{company_name} contact',
            f'{company_name} locations',
            f'{company_name} careers',
            f'{company_name} jobs',
            f'{company_name} news',
            f'{company_name} press releases',
            f'{company_name} blog',
            f'{company_name} docs',
            f'{company_name} developers',
            f'{company_name} api',
            f'{company_name} github',
            f'{company_name} linkedin',
            f'{company_name} x',
            f'{company_name} youtube',
            f'{company_name} sustainability',
            f'{company_name} esg',
            f'{company_name} patents',
            f'{company_name} competitors',
            f'{company_name} technology',
            f'{company_name} acquisitions',
            f'{company_name} partnerships',
            f'{company_name} stock price',
            f'{company_name} market cap',
            f'{company_name} funding',
            f'{company_name} valuation',
            f'{company_name} shop',
            f'{company_name} store',
            f'{company_name} customer stories',
            f'{company_name} case studies',
            f'{company_name} support',
            f'{company_name} security',
            f'{company_name} privacy',
            f'{company_name} terms',
            f'{company_name} investors',
        ]
        if website:
            queries.insert(0, f'{company_name} {website}')
        return dedupe_preserve_order(queries)

    def _parse_results(self, payload: dict[str, Any]) -> list[SearchResult]:
        organic = payload.get('organic', []) or []
        results: list[SearchResult] = []
        for item in organic:
            link = normalize_url(str(item.get('link', '')).strip())
            title = normalize_whitespace(str(item.get('title', '')).strip())
            snippet = normalize_whitespace(str(item.get('snippet', '')).strip())
            if link and title:
                results.append(SearchResult(title=title, link=link, snippet=snippet))
        return results

    def _looks_official(self, url: str, tokens: set[str]) -> bool:
        host = domain_from_url(url)
        if not host or any(blocked in host for blocked in EXCLUDED_HOSTS):
            return False
        if not tokens:
            return True
        host_tokens = set(host.replace('-', ' ').replace('.', ' ').split())
        return bool(tokens & host_tokens) or any(token in host for token in tokens)

    def _domain_tokens(self, company_name: str) -> set[str]:
        tokens = {token for token in normalize_whitespace(company_name).lower().split() if len(token) > 2}
        return tokens

    def _dedupe_sources(self, sources: list[ResearchSource]) -> list[ResearchSource]:
        seen: set[str] = set()
        deduped: list[ResearchSource] = []
        for source in sources:
            key = source.url.lower().strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(source)
        return deduped
