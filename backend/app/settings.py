from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Relu Company Research Assistant'
    app_version: str = '1.0.0'
    api_prefix: str = '/api'
    cors_origins: list[str] = Field(default_factory=lambda: ['http://localhost:5173', 'http://127.0.0.1:5173'])

    request_timeout_seconds: float = 20.0
    crawl_timeout_seconds: float = 25.0
    crawl_max_pages: int = 8
    crawl_max_depth: int = 2
    crawl_concurrency: int = 4
    crawl_user_agent: str = 'ReluResearchBot/1.0 (+https://relu.ai)'

    groq_base_url: str = 'https://api.groq.com/openai/v1'
    serper_base_url: str = 'https://google.serper.dev'
    groq_default_model: str = 'llama-3.1-70b-versatile'

    discord_api_base_url: str = 'https://discord.com/api/v10'
    report_footer_text: str = 'Generated using AI Company Research Assistant'

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
