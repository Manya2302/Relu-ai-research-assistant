from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

EMAIL_RE = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE_RE = re.compile(r'(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}')
WHITESPACE_RE = re.compile(r'[\t\r\f\v ]+')
MULTILINE_RE = re.compile(r'\n{3,}')
TRACKING_PARAMS = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'fbclid'}


def normalize_whitespace(text: str) -> str:
    if not text:
        return ''
    text = text.replace('\xa0', ' ')
    text = WHITESPACE_RE.sub(' ', text)
    text = re.sub(r' *\n *', '\n', text)
    text = MULTILINE_RE.sub('\n\n', text)
    return text.strip()


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def extract_emails(text: str) -> list[str]:
    return dedupe_preserve_order(EMAIL_RE.findall(text or ''))


def extract_phone_numbers(text: str) -> list[str]:
    values = [match.strip() for match in PHONE_RE.findall(text or '')]
    cleaned = []
    for value in values:
        digits = re.sub(r'\D', '', value)
        if 7 <= len(digits) <= 16:
            if len(digits) == 8 and (digits.startswith('19') or digits.startswith('20')):
                continue
            # Reject raw strings of digits (no formatting) unless they are exactly 10-15 digits or start with +
            if value.isdigit() and not value.startswith('+') and len(value) < 10:
                continue
            cleaned.append(value)
    return dedupe_preserve_order(cleaned)


def remove_tracking_params(url: str) -> str:
    parsed = urlparse(url)
    query = '&'.join(
        pair for pair in parsed.query.split('&') if pair and pair.split('=')[0] not in TRACKING_PARAMS
    )
    return urlunparse(parsed._replace(query=query, fragment=''))


def sanitize_text_block(text: str) -> str:
    text = normalize_whitespace(text)
    return text.replace('  ', ' ').strip()


def safe_strip(value: str | None) -> str:
    return value.strip() if isinstance(value, str) else ''
