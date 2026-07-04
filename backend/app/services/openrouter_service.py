from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.config import SYSTEM_PROMPT
from app.schemas.research import CompanyResearchContext, CompanyResearchResult, Competitor, ModelInfo, LeadershipInfo
from app.settings import get_settings
from app.utils.cleaner import dedupe_preserve_order, normalize_whitespace
from app.utils.helpers import safe_filename, truncate_text

logger = logging.getLogger(__name__)


class GroqService:
    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key.strip()
        
        if not base_url:
            if self.api_key.startswith('gsk_'):
                self.base_url = 'https://api.groq.com/openai/v1'
            elif self.api_key.startswith('sk-or-'):
                self.base_url = 'https://openrouter.ai/api/v1'
            elif self.api_key.startswith('sk-proj-') or (self.api_key.startswith('sk-') and not self.api_key.startswith('sk-ant-')):
                self.base_url = 'https://api.openai.com/v1'
            elif self.api_key.startswith('AIza'):
                self.base_url = 'https://generativelanguage.googleapis.com/v1beta/openai'
            else:
                self.base_url = settings.groq_base_url.rstrip('/')
        else:
            self.base_url = base_url.rstrip('/')
            
        self.timeout = settings.request_timeout_seconds
        self.default_model = settings.groq_default_model

    async def list_models(self) -> list[ModelInfo]:
        if not self.api_key:
            raise ValueError('Groq API key is required.')
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f'{self.base_url}/models', headers=headers)
            response.raise_for_status()
            data = response.json()
        models: list[ModelInfo] = []
        for item in data.get('data', []):
            model_id = str(item.get('id', '')).strip()
            if not model_id:
                continue
            models.append(
                ModelInfo(
                    id=model_id,
                    object=str(item.get('object', 'model')),
                    owned_by=str(item.get('owned_by', 'groq')),
                    label=model_id,
                )
            )
        return models

    async def generate_research(self, model: str, context: CompanyResearchContext) -> CompanyResearchResult:
        if not self.api_key:
            raise ValueError('Groq API key is required.')
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = None
            for mode in ('full', 'compact', 'ultra'):
                response = await client.post(
                    f'{self.base_url}/chat/completions',
                    headers=headers,
                    json=self._build_payload(model or self.default_model, context, mode=mode),
                )
                
                if response.status_code == 200:
                    break
                    
                error_text = response.text.lower()
                logger.warning(f"Groq API returned {response.status_code}: {response.text}")
                
                if response.status_code in (413, 400) and ("too large" in error_text or "token" in error_text or "context length" in error_text or "exceeds" in error_text):
                    logger.warning(f'Groq payload was too large for mode={mode}, retrying with smaller context.')
                    continue
                else:
                    break
                    
            assert response is not None
            if response.status_code != 200:
                raise Exception(f"Groq API Error: {response.text}")
            
            raw_content = response.json()['choices'][0]['message']['content']

        data = self._parse_json_payload(raw_content)
        return self._to_result(data, context)

    def _build_payload(self, model: str, context: CompanyResearchContext, mode: str) -> dict[str, Any]:
        compact = mode in {'compact', 'ultra'}
        ultra = mode == 'ultra'
        payload = {
            'company_name': context.company_name,
            'website': context.website,
            'query': context.query,
            'structured_text': self._compact_structured_text(context.structured_text, compact=compact, ultra=ultra),
            'knowledge_graph': self._compact_knowledge_graph(context.knowledge_graph.model_dump(), compact=compact, ultra=ultra),
            'search_sources': self._compact_sources(context.search_sources, limit=2 if ultra else 6 if compact else 10),
            'public_sources': self._compact_sources(context.public_sources, limit=4 if ultra else 8 if compact else 14),
            'inferred_country': context.inferred_country,
            'inferred_industry': context.inferred_industry,
        }
        return {
            'model': model,
            'temperature': 0.2,
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': self._build_prompt_text(payload, compact=compact)},
            ],
            'response_format': {'type': 'json_object'},
        }

    def _build_prompt_text(self, payload: dict[str, Any], compact: bool) -> str:
        prefix = (
            'Analyze this company research context and return the required JSON object only.'
            if not compact
            else 'Analyze this compact company research context and return the required JSON object only.'
        )
        return f'{prefix}\n\n{json.dumps(payload, ensure_ascii=False, indent=2)}'

    def _compact_sources(self, sources: list[Any], limit: int) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for source in sources[:limit]:
            items.append(
                {
                    'title': truncate_text(normalize_whitespace(getattr(source, 'title', '')), 120),
                    'url': truncate_text(normalize_whitespace(getattr(source, 'url', '')), 180),
                    'snippet': truncate_text(normalize_whitespace(getattr(source, 'snippet', '')), 220),
                }
            )
        return items

    def _compact_structured_text(self, structured_text: dict[str, list[str]], compact: bool, ultra: bool = False) -> dict[str, list[str]]:
        limits = {
            'headings': 6 if ultra else 12 if compact else 20,
            'paragraphs': 6 if ultra else 12 if compact else 24,
            'lists': 6 if ultra else 12 if compact else 20,
            'emails': 2 if ultra else 4 if compact else 6,
            'phones': 2 if ultra else 4 if compact else 6,
            'addresses': 2 if ultra else 4 if compact else 6,
        }
        compacted: dict[str, list[str]] = {}
        for key, values in structured_text.items():
            compacted[key] = [truncate_text(normalize_whitespace(value), 160) for value in values[: limits.get(key, 8)]]
        return compacted

    def _compact_knowledge_graph(self, knowledge_graph: dict[str, list[str]], compact: bool, ultra: bool = False) -> dict[str, list[str]]:
        limits = {
            'profile': 2 if ultra else 4 if compact else 6,
            'leadership': 2 if ultra else 4 if compact else 6,
            'financials': 2 if ultra else 4 if compact else 6,
            'products': 3 if ultra else 5 if compact else 8,
            'services': 3 if ultra else 5 if compact else 8,
            'pricing': 2 if ultra else 4 if compact else 6,
            'locations': 2 if ultra else 4 if compact else 6,
            'offices': 2 if ultra else 4 if compact else 6,
            'employees': 1 if ultra else 2 if compact else 4,
            'careers': 2 if ultra else 4 if compact else 8,
            'customers': 2 if ultra else 4 if compact else 8,
            'partners': 2 if ultra else 4 if compact else 6,
            'investors': 2 if ultra else 4 if compact else 6,
            'news': 3 if ultra else 6 if compact else 10,
            'events': 2 if ultra else 4 if compact else 6,
            'blogs': 2 if ultra else 4 if compact else 6,
            'patents': 2 if ultra else 4 if compact else 6,
            'technology': 3 if ultra else 5 if compact else 8,
            'social_media': 3 if ultra else 5 if compact else 8,
            'competitors': 3 if ultra else 5 if compact else 8,
            'shop': 3 if ultra else 5 if compact else 8,
            'downloads': 2 if ultra else 4 if compact else 6,
            'case_studies': 2 if ultra else 4 if compact else 8,
            'research': 2 if ultra else 4 if compact else 6,
        }
        compacted: dict[str, list[str]] = {}
        for key, values in knowledge_graph.items():
            compacted[key] = [truncate_text(normalize_whitespace(value), 140) for value in values[: limits.get(key, 5)]]
        return compacted

    def _parse_json_payload(self, content: str) -> dict[str, Any]:
        cleaned = content.strip()
        cleaned = re.sub(r'^```json\s*', '', cleaned)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start >= 0 and end > start:
                return json.loads(cleaned[start : end + 1])
            raise

    def _to_result(self, payload: dict[str, Any], context: CompanyResearchContext) -> CompanyResearchResult:
        competitors = [
            Competitor(
                name=normalize_whitespace(str(item.get('name', '')).strip()),
                website=normalize_whitespace(str(item.get('website', '')).strip()),
                reason=normalize_whitespace(str(item.get('reason', '')).strip()),
            )
            for item in payload.get('competitors', []) or []
            if str(item.get('name', '')).strip()
        ]
        competitors = self._dedupe_competitors(competitors)
        
        raw_leadership = payload.get('leadership_info') or {}
        leadership_info = LeadershipInfo(
            ceo=normalize_whitespace(str(raw_leadership.get('ceo', '')).strip()),
            cfo=normalize_whitespace(str(raw_leadership.get('cfo', '')).strip()),
            cto=normalize_whitespace(str(raw_leadership.get('cto', '')).strip()),
            founders=dedupe_preserve_order([str(item).strip() for item in raw_leadership.get('founders', []) or []]),
            board_members=dedupe_preserve_order([str(item).strip() for item in raw_leadership.get('board_members', []) or []]),
        )

        return CompanyResearchResult(
            company_name=normalize_whitespace(str(payload.get('company_name') or context.company_name)),
            summary=normalize_whitespace(str(payload.get('summary', '')).strip()),
            website=normalize_whitespace(str(payload.get('website') or context.website)),
            phone=normalize_whitespace(str(payload.get('phone', '')).strip()),
            address=normalize_whitespace(str(payload.get('address', '')).strip()),
            revenue=normalize_whitespace(str(payload.get('revenue', '')).strip()),
            market_cap=normalize_whitespace(str(payload.get('market_cap', '')).strip()),
            funding=normalize_whitespace(str(payload.get('funding', '')).strip()),
            products=dedupe_preserve_order([str(item).strip() for item in payload.get('products', []) or []]),
            pain_points=dedupe_preserve_order([str(item).strip() for item in payload.get('pain_points', []) or []]),
            recommendations=dedupe_preserve_order([str(item).strip() for item in payload.get('recommendations', []) or []]),
            industry=normalize_whitespace(str(payload.get('industry') or context.inferred_industry)),
            country=normalize_whitespace(str(payload.get('country') or context.inferred_country)),
            leadership_info=leadership_info,
            competitors=competitors,
            report_filename=safe_filename(normalize_whitespace(str(payload.get('company_name') or context.company_name))),
        )

    def _dedupe_competitors(self, competitors: list[Competitor]) -> list[Competitor]:
        seen: set[str] = set()
        result: list[Competitor] = []
        for competitor in competitors:
            key = competitor.name.lower().strip()
            if key and key not in seen:
                seen.add(key)
                result.append(competitor)
        return result
