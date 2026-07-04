from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from urllib.parse import urljoin, urlparse, urlunparse

from .cleaner import remove_tracking_params

PUBLIC_SCHEME = {'http', 'https'}


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ''
    parsed = urlparse(value if '://' in value else f'https://{value}')
    scheme = parsed.scheme.lower() or 'https'
    netloc = parsed.netloc.lower()
    path = parsed.path or '/'
    if path and not path.startswith('/'):
        path = f'/{path}'
    normalized = urlunparse((scheme, netloc, path.rstrip('/') or '/', '', parsed.query, ''))
    return remove_tracking_params(normalized)


def ensure_http_url(value: str) -> str:
    return normalize_url(value)


def is_public_hostname(hostname: str) -> bool:
    hostname = (hostname or '').lower().strip('.')
    if not hostname or hostname in {'localhost'}:
        return False
    try:
        ip = ipaddress.ip_address(hostname)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
    except ValueError:
        return True


def is_valid_research_url(value: str) -> bool:
    parsed = urlparse(value if '://' in value else f'https://{value}')
    if parsed.scheme.lower() not in PUBLIC_SCHEME:
        return False
    return bool(parsed.netloc) and is_public_hostname(parsed.hostname or '')


def is_company_name_query(value: str) -> bool:
    if not value:
        return False
    return not re.match(r'^(https?://)?[\w.-]+\.[A-Za-z]{2,}', value.strip())


def guess_company_name_from_url(value: str) -> str:
    parsed = urlparse(value if '://' in value else f'https://{value}')
    host = parsed.hostname or ''
    parts = [segment for segment in host.replace('www.', '').split('.') if segment]
    if parts:
        candidate = parts[0]
        return candidate.replace('-', ' ').replace('_', ' ').title()
    return ''


def domain_from_url(value: str) -> str:
    parsed = urlparse(value if '://' in value else f'https://{value}')
    return (parsed.hostname or '').lower().removeprefix('www.')


def safe_join_url(base_url: str, href: str) -> str:
    return remove_tracking_params(urljoin(base_url, href))


def unique_by(items: list[dict], key_name: str) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for item in items:
        key = str(item.get(key_name, '')).strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def stable_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def truncate_text(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return f'{text[:limit].rstrip()}...'


def safe_filename(name: str, suffix: str = '.pdf') -> str:
    sanitized = re.sub(r'[^A-Za-z0-9._-]+', '-', name.strip().lower()) or 'company-research-report'
    return f'{sanitized[:80].strip("-")}{suffix}'
