from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Competitor(BaseModel):
    name: str = ''
    website: str = ''
    reason: str = ''


class LeadershipInfo(BaseModel):
    ceo: str = ''
    cfo: str = ''
    cto: str = ''
    founders: list[str] = Field(default_factory=list)
    board_members: list[str] = Field(default_factory=list)


class ResearchSource(BaseModel):
    title: str = ''
    url: str = ''
    snippet: str = ''


class CrawledPage(BaseModel):
    url: str
    title: str = ''
    meta_description: str = ''
    headings: list[str] = Field(default_factory=list)
    paragraphs: list[str] = Field(default_factory=list)
    lists: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    addresses: list[str] = Field(default_factory=list)
    text: str = ''


class DiscordSettings(BaseModel):
    bot_token: str = ''
    channel_id: str = ''
    applicant_name: str = ''
    applicant_email: str = ''


class ResearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    input_type: Literal['company_name', 'website_url'] = 'company_name'
    groq_api_key: str = Field(min_length=10)
    serper_api_key: str = Field(min_length=10)
    model: str = Field(min_length=1)
    discord: DiscordSettings | None = None

    @field_validator('query')
    @classmethod
    def strip_query(cls, value: str) -> str:
        return value.strip()


class ModelListRequest(BaseModel):
    groq_api_key: str = Field(min_length=10)


class ModelInfo(BaseModel):
    id: str
    object: str = 'model'
    owned_by: str = ''
    label: str = ''


class CompanyResearchResult(BaseModel):
    company_name: str = ''
    summary: str = ''
    website: str = ''
    phone: str = ''
    address: str = ''
    revenue: str = ''
    market_cap: str = ''
    funding: str = ''
    products: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    industry: str = ''
    country: str = ''
    leadership_info: LeadershipInfo | None = None
    competitors: list[Competitor] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)
    references: list[ResearchSource] = Field(default_factory=list)
    knowledge_graph: CompanyKnowledgeGraph = Field(default_factory=lambda: CompanyKnowledgeGraph())
    crawler_pages: list[CrawledPage] = Field(default_factory=list)
    crawler_stats: dict[str, int] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    pdf_base64: str = ''
    report_filename: str = ''


class CompanyKnowledgeGraph(BaseModel):
    profile: list[str] = Field(default_factory=list)
    leadership: list[str] = Field(default_factory=list)
    financials: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    pricing: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    offices: list[str] = Field(default_factory=list)
    employees: list[str] = Field(default_factory=list)
    careers: list[str] = Field(default_factory=list)
    customers: list[str] = Field(default_factory=list)
    partners: list[str] = Field(default_factory=list)
    investors: list[str] = Field(default_factory=list)
    news: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    blogs: list[str] = Field(default_factory=list)
    patents: list[str] = Field(default_factory=list)
    technology: list[str] = Field(default_factory=list)
    social_media: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    shop: list[str] = Field(default_factory=list)
    downloads: list[str] = Field(default_factory=list)
    case_studies: list[str] = Field(default_factory=list)
    research: list[str] = Field(default_factory=list)


class ProgressEvent(BaseModel):
    stage: str
    message: str
    progress: int = 0
    done: bool = False
    result: CompanyResearchResult | None = None
    error: str = ''


class CompanyResearchContext(BaseModel):
    company_name: str = ''
    website: str = ''
    official_website: str = ''
    query: str = ''
    search_sources: list[ResearchSource] = Field(default_factory=list)
    public_sources: list[ResearchSource] = Field(default_factory=list)
    pages: list[CrawledPage] = Field(default_factory=list)
    extracted_text: str = ''
    structured_text: dict[str, list[str]] = Field(default_factory=dict)
    knowledge_graph: CompanyKnowledgeGraph = Field(default_factory=CompanyKnowledgeGraph)
    inferred_country: str = ''
    inferred_industry: str = ''
