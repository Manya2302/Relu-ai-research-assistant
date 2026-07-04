from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

import httpx

from app.config import IGNORED_PATH_SEGMENTS, IMPORTANT_PATHS
from app.settings import get_settings
from app.utils.cleaner import dedupe_preserve_order
from app.utils.extractor import extract_page_content
from app.utils.helpers import is_public_hostname, normalize_url, safe_join_url

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FetchedPage:
    url: str
    html: str


class WebsiteCrawler:
    def __init__(self, max_pages: int | None = None, max_depth: int | None = None) -> None:
        settings = get_settings()
        self.max_pages = max_pages or settings.crawl_max_pages
        self.max_depth = max_depth or settings.crawl_max_depth
        self.timeout = settings.crawl_timeout_seconds
        self.user_agent = settings.crawl_user_agent
        self.concurrency = settings.crawl_concurrency

    async def crawl(self, website_url: str) -> list:
        base_url = normalize_url(website_url)
        parsed = urlparse(base_url)
        if not parsed.scheme or not parsed.hostname or not is_public_hostname(parsed.hostname):
            raise ValueError('The provided website URL is not publicly reachable.')

        visited: set[str] = set()
        pages = []
        frontier = self._seed_urls(base_url)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers={'User-Agent': self.user_agent}) as client:
            for depth in range(self.max_depth + 1):
                if not frontier or len(pages) >= self.max_pages:
                    break
                batch = [url for url in frontier if url not in visited]
                if not batch:
                    break
                visited.update(batch)
                fetch_results = await self._fetch_batch(client, batch[: self.max_pages - len(pages)])
                next_frontier: list[str] = []
                for fetched in fetch_results:
                    if not fetched:
                        continue
                    extracted = extract_page_content(fetched.html, fetched.url)
                    pages.append(extracted)
                    if len(pages) >= self.max_pages:
                        break
                    next_frontier.extend(self._discover_links(fetched.html, fetched.url))
                frontier = self._merge_frontier(base_url, next_frontier, visited)

        return pages[: self.max_pages]

    async def _fetch_batch(self, client: httpx.AsyncClient, urls: list[str]) -> list[FetchedPage | None]:
        semaphore = asyncio.Semaphore(self.concurrency)

        async def runner(url: str) -> FetchedPage | None:
            async with semaphore:
                return await self._fetch_page(client, url)

        return await asyncio.gather(*(runner(url) for url in urls))

    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> FetchedPage | None:
        try:
            response = await client.get(url)
            html = ''
            content_type = response.headers.get('content-type', '').lower()
            if response.status_code < 400 and response.text.strip():
                html = response.text
            if 'text/html' not in content_type and not html:
                html = await self._playwright_fallback(url)
            if not html and response.status_code < 500:
                html = response.text
            if not html:
                return None
            if self._looks_blocked(html):
                logger.warning('Crawler detected blocked content for %s', url)
                return None
            return FetchedPage(url=str(response.url), html=html)
        except Exception as exc:
            logger.warning('Crawler fetch failed for %s: %s', url, exc)
            html = await self._playwright_fallback(url)
            if html and not self._looks_blocked(html):
                return FetchedPage(url=url, html=html)
            return None

    async def _playwright_fallback(self, url: str) -> str:
        try:
            from playwright.async_api import async_playwright
        except Exception:
            return ''
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=self.user_agent)
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=int(self.timeout * 1000))
                    await page.wait_for_load_state('networkidle', timeout=5000)
                except Exception:
                    pass
                html = await page.content()
                await browser.close()
                return html
        except Exception as exc:
            logger.warning('Playwright fallback failed for %s: %s', url, exc)
            return ''

    def _seed_urls(self, base_url: str) -> list[str]:
        seeds = [normalize_url(base_url)]
        for path in IMPORTANT_PATHS[1:]:
            seeds.append(safe_join_url(base_url, path))
        return dedupe_preserve_order(seeds)

    def _discover_links(self, html: str, source_url: str) -> list[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html or '', 'lxml')
        links: list[str] = []
        for anchor in soup.find_all('a', href=True):
            href = str(anchor.get('href', '')).strip()
            if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                continue
            absolute = safe_join_url(source_url, href)
            if self._should_visit(absolute, source_url):
                links.append(absolute)
        return dedupe_preserve_order(links)

    def _merge_frontier(self, base_url: str, urls: Iterable[str], visited: set[str]) -> list[str]:
        merged = [normalize_url(url) for url in urls if self._should_visit(url, base_url) and url not in visited]
        return dedupe_preserve_order(merged)[: self.max_pages]

    def _should_visit(self, url: str, base_url: str) -> bool:
        normalized = normalize_url(url)
        if not normalized:
            return False
        parsed = urlparse(normalized)
        base_host = (urlparse(base_url).hostname or '').lower().removeprefix('www.')
        current_host = (parsed.hostname or '').lower().removeprefix('www.')
        if not current_host or not self._same_site(current_host, base_host):
            return False
        path = parsed.path.lower()
        if any(segment in path for segment in IGNORED_PATH_SEGMENTS):
            return False
        if self._looks_like_asset(path):
            return False
        return True

    def _same_site(self, current_host: str, base_host: str) -> bool:
        return current_host == base_host or current_host.endswith(f'.{base_host}') or base_host.endswith(f'.{current_host}')

    def _looks_like_asset(self, path: str) -> bool:
        asset_suffixes = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.mp4', '.mp3', '.zip', '.rar', '.json', '.xml', '.css', '.js')
        return path.endswith(asset_suffixes)

    def _looks_blocked(self, html: str) -> bool:
        text = (html or '').lower()
        blocked_markers = (
            'access denied',
            'permission to access',
            'captcha',
            'verify you are human',
            'robot check',
            'cloudflare',
            'request blocked',
            '403 forbidden',
        )
        return any(marker in text for marker in blocked_markers)
