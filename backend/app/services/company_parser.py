from __future__ import annotations

from urllib.parse import urlparse

from app.schemas.research import CompanyKnowledgeGraph, CompanyResearchContext, CrawledPage, ResearchSource
from app.utils.cleaner import dedupe_preserve_order, normalize_whitespace
from app.utils.helpers import guess_company_name_from_url

INDUSTRY_HINTS = {
    'software': ('software', 'platform', 'cloud', 'saas', 'developer', 'api'),
    'healthcare': ('health', 'medical', 'clinic', 'hospital', 'pharma', 'healthcare'),
    'finance': ('bank', 'finance', 'financial', 'investment', 'payment', 'lending'),
    'ecommerce': ('shop', 'store', 'commerce', 'retail', 'marketplace'),
    'manufacturing': ('manufacturing', 'factory', 'industrial', 'equipment', 'engineering'),
    'consulting': ('consulting', 'advisory', 'strategy', 'services'),
}

COUNTRY_HINTS = {
    'us': ('united states', 'usa', 'new york', 'california', 'texas', 'seattle', 'san francisco'),
    'uk': ('united kingdom', 'london', 'manchester', 'england'),
    'in': ('india', 'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai'),
    'ca': ('canada', 'toronto', 'vancouver', 'montreal'),
}


class CompanyParser:
    def build_context(
        self,
        query: str,
        official_website: str,
        search_sources: list[ResearchSource],
        public_sources: list[ResearchSource],
        pages: list[CrawledPage],
    ) -> CompanyResearchContext:
        company_name = self._infer_company_name(query, official_website, pages, search_sources)
        structured_text = self._build_structured_text(pages)
        extracted_text = self._build_text_digest(pages, search_sources, public_sources)
        knowledge_graph = self._build_knowledge_graph(company_name, official_website, pages, search_sources, public_sources)
        country = self._infer_country(pages, public_sources)
        industry = self._infer_industry(pages, search_sources, public_sources)

        return CompanyResearchContext(
            company_name=company_name,
            website=official_website,
            official_website=official_website,
            query=query,
            search_sources=search_sources,
            public_sources=public_sources,
            pages=pages,
            extracted_text=extracted_text,
            structured_text=structured_text,
            knowledge_graph=knowledge_graph,
            inferred_country=country,
            inferred_industry=industry,
        )

    def _infer_company_name(
        self,
        query: str,
        website: str,
        pages: list[CrawledPage],
        sources: list[ResearchSource],
    ) -> str:
        if query and not self._looks_like_url(query):
            return normalize_whitespace(query)
        candidates = [page.title for page in pages if page.title]
        candidates.extend(source.title for source in sources if source.title)
        if candidates:
            return self._cleanup_name(candidates[0])
        return self._cleanup_name(guess_company_name_from_url(website or query))

    def _build_structured_text(self, pages: list[CrawledPage]) -> dict[str, list[str]]:
        headings: list[str] = []
        paragraphs: list[str] = []
        lists: list[str] = []
        emails: list[str] = []
        phones: list[str] = []
        addresses: list[str] = []
        for page in pages:
            headings.extend(page.headings)
            paragraphs.extend(page.paragraphs)
            lists.extend(page.lists)
            emails.extend(page.emails)
            phones.extend(page.phone_numbers)
            addresses.extend(page.addresses)
        return {
            'headings': dedupe_preserve_order(headings)[:24],
            'paragraphs': dedupe_preserve_order(paragraphs)[:30],
            'lists': dedupe_preserve_order(lists)[:24],
            'emails': dedupe_preserve_order(emails)[:8],
            'phones': dedupe_preserve_order(phones)[:8],
            'addresses': dedupe_preserve_order(addresses)[:8],
        }

    def _build_knowledge_graph(
        self,
        company_name: str,
        official_website: str,
        pages: list[CrawledPage],
        search_sources: list[ResearchSource],
        public_sources: list[ResearchSource],
    ) -> CompanyKnowledgeGraph:
        sources = search_sources + public_sources
        profile = self._collect_fields(company_name, official_website, pages, sources, keywords=('about', 'company', 'profile', 'mission', 'vision', 'history', 'overview'))
        leadership = self._collect_fields(company_name, official_website, pages, sources, keywords=('leadership', 'team', 'executive', 'board', 'ceo', 'founder', 'management'))
        financials = self._collect_fields(company_name, official_website, pages, sources, keywords=('financial', 'revenue', 'earnings', 'income', 'investor', 'annual report', '10-k', '10-q', 'valuation', 'market cap'))
        products = self._collect_fields(company_name, official_website, pages, sources, keywords=('product', 'platform', 'solution', 'service', 'offering', 'catalog', 'pricing', 'plans'))
        services = self._collect_fields(company_name, official_website, pages, sources, keywords=('services', 'consulting', 'support', 'implementation', 'managed', 'professional services'))
        pricing = self._collect_fields(company_name, official_website, pages, sources, keywords=('pricing', 'plans', 'subscription', 'cost', 'quote', 'license'))
        locations = self._collect_fields(company_name, official_website, pages, sources, keywords=('locations', 'office', 'headquarters', 'contact', 'address', 'global', 'regional'))
        offices = self._collect_fields(company_name, official_website, pages, sources, keywords=('office', 'campus', 'hq', 'headquarters', 'branch'))
        employees = self._collect_fields(company_name, official_website, pages, sources, keywords=('employees', 'headcount', 'people', 'team size', 'workforce'))
        careers = self._collect_fields(company_name, official_website, pages, sources, keywords=('careers', 'jobs', 'hiring', 'open positions', 'join us', 'vacancies'))
        customers = self._collect_fields(company_name, official_website, pages, sources, keywords=('customers', 'clients', 'case study', 'success story', 'testimonials', 'partners'))
        partners = self._collect_fields(company_name, official_website, pages, sources, keywords=('partners', 'ecosystem', 'alliances', 'integrations'))
        investors = self._collect_fields(company_name, official_website, pages, sources, keywords=('investor', 'shareholder', 'stock', 'ir', 'filings'))
        news = self._collect_fields(company_name, official_website, pages, sources, keywords=('news', 'press', 'release', 'media', 'announcement'))
        events = self._collect_fields(company_name, official_website, pages, sources, keywords=('events', 'webinar', 'conference', 'summit'))
        blogs = self._collect_fields(company_name, official_website, pages, sources, keywords=('blog', 'insights', 'articles', 'resources'))
        patents = self._collect_fields(company_name, official_website, pages, sources, keywords=('patent', 'intellectual property', 'ip', 'invention'))
        technology = self._collect_fields(company_name, official_website, pages, sources, keywords=('technology', 'tech stack', 'api', 'sdk', 'developer', 'open source', 'platform'))
        social_media = self._collect_fields(company_name, official_website, pages, sources, keywords=('linkedin', 'x.com', 'twitter', 'youtube', 'instagram', 'facebook', 'social'))
        competitors = self._collect_fields(company_name, official_website, pages, sources, keywords=('competitor', 'alternatives', 'compare', 'vs', 'benchmark'))
        shop = self._collect_fields(company_name, official_website, pages, sources, keywords=('shop', 'store', 'products', 'cart', 'checkout', 'merchandise'))
        downloads = self._collect_fields(company_name, official_website, pages, sources, keywords=('download', 'pdf', 'brochure', 'datasheet', 'whitepaper'))
        case_studies = self._collect_fields(company_name, official_website, pages, sources, keywords=('case study', 'success story', 'customer story', 'use case'))
        research = self._collect_fields(company_name, official_website, pages, sources, keywords=('research', 'lab', 'labs', 'papers', 'publications'))

        return CompanyKnowledgeGraph(
            profile=profile[:6],
            leadership=leadership[:6],
            financials=financials[:6],
            products=products[:8],
            services=services[:8],
            pricing=pricing[:6],
            locations=locations[:6],
            offices=offices[:6],
            employees=employees[:4],
            careers=careers[:8],
            customers=customers[:8],
            partners=partners[:6],
            investors=investors[:6],
            news=news[:10],
            events=events[:6],
            blogs=blogs[:6],
            patents=patents[:6],
            technology=technology[:8],
            social_media=social_media[:8],
            competitors=competitors[:8],
            shop=shop[:8],
            downloads=downloads[:6],
            case_studies=case_studies[:8],
            research=research[:6],
        )

    def _build_text_digest(self, pages: list[CrawledPage], search_sources: list[ResearchSource], public_sources: list[ResearchSource]) -> str:
        chunks: list[str] = []
        for page in pages:
            block = '\n'.join(part for part in [page.title, page.meta_description, page.text] if part)
            chunks.append(block)
        for source in search_sources + public_sources:
            chunks.append(' | '.join(part for part in [source.title, source.snippet, source.url] if part))
        return normalize_whitespace('\n\n'.join(chunk for chunk in chunks if chunk))

    def _infer_industry(self, pages: list[CrawledPage], *source_groups: list[ResearchSource]) -> str:
        tokens = self._collect_tokens(pages, source_groups)
        for industry, keywords in INDUSTRY_HINTS.items():
            if any(keyword in tokens for keyword in keywords):
                return industry.title()
        return ''

    def _infer_country(self, pages: list[CrawledPage], *source_groups: list[ResearchSource]) -> str:
        text = self._collect_text(pages, source_groups).lower()
        for country, keywords in COUNTRY_HINTS.items():
            if any(keyword in text for keyword in keywords):
                return country.upper()
        return ''

    def _collect_tokens(self, pages: list[CrawledPage], source_groups: tuple[list[ResearchSource], ...]) -> set[str]:
        text = self._collect_text(pages, source_groups).lower()
        return {token for token in text.replace('/', ' ').replace('-', ' ').split() if token}

    def _collect_text(self, pages: list[CrawledPage], source_groups: tuple[list[ResearchSource], ...]) -> str:
        parts = [page.text for page in pages]
        for group in source_groups:
            parts.extend([item.title + ' ' + item.snippet for item in group])
        return ' '.join(parts)

    def _collect_fields(
        self,
        company_name: str,
        official_website: str,
        pages: list[CrawledPage],
        sources: list[ResearchSource],
        keywords: tuple[str, ...],
    ) -> list[str]:
        matches: list[str] = []
        corpus = self._collect_text(pages, (sources,)).lower()
        for keyword in keywords:
            if keyword.lower() in corpus:
                matches.append(keyword.title())
        for page in pages:
            page_hints = ' '.join([page.url, page.title, page.meta_description] + page.headings).lower()
            if any(keyword.lower() in page_hints for keyword in keywords):
                matches.append(page.title or page.url)
        for source in sources:
            if any(keyword.lower() in (source.title + ' ' + source.snippet).lower() for keyword in keywords):
                matches.append(source.title or source.url)
        if official_website:
            base = urlparse(official_website).netloc
            matches.append(base)
        if company_name:
            matches.append(company_name)
        return dedupe_preserve_order(matches)[:20]

    def _looks_like_url(self, value: str) -> bool:
        return bool(urlparse(value if '://' in value else f'https://{value}').netloc)

    def _cleanup_name(self, value: str) -> str:
        value = normalize_whitespace(value)
        value = value.replace('|', ' ').replace('Home', '').strip()
        return value[:120]
