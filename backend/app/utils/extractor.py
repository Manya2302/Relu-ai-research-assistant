from __future__ import annotations

from bs4 import BeautifulSoup, Comment

from app.schemas.research import CrawledPage
from .cleaner import dedupe_preserve_order, extract_emails, extract_phone_numbers, normalize_whitespace

REMOVED_TAGS = ('script', 'style', 'noscript', 'svg', 'canvas', 'iframe', 'form', 'nav', 'footer', 'header', 'aside')


def extract_page_content(html: str, url: str) -> CrawledPage:
    soup = BeautifulSoup(html or '', 'lxml')
    for tag_name in REMOVED_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    title = normalize_whitespace(soup.title.get_text(' ', strip=True)) if soup.title else ''
    meta_description = ''
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag and meta_tag.get('content'):
        meta_description = normalize_whitespace(str(meta_tag.get('content', '')))

    headings = []
    for heading_tag in ('h1', 'h2', 'h3'):
        headings.extend(normalize_whitespace(tag.get_text(' ', strip=True)) for tag in soup.find_all(heading_tag))

    paragraph_text = [normalize_whitespace(tag.get_text(' ', strip=True)) for tag in soup.find_all('p')]
    list_text = [normalize_whitespace(tag.get_text(' ', strip=True)) for tag in soup.find_all(['li'])]
    body_text = normalize_whitespace(soup.get_text('\n', strip=True))
    emails = extract_emails(body_text)
    phone_numbers = extract_phone_numbers(body_text)
    addresses = _extract_addresses(soup)

    return CrawledPage(
        url=url,
        title=title,
        meta_description=meta_description,
        headings=dedupe_preserve_order([text for text in headings if text]),
        paragraphs=dedupe_preserve_order([text for text in paragraph_text if text]),
        lists=dedupe_preserve_order([text for text in list_text if text]),
        emails=emails,
        phone_numbers=phone_numbers,
        addresses=addresses,
        text=body_text,
    )


def _extract_addresses(soup: BeautifulSoup) -> list[str]:
    candidates: list[str] = []
    for tag in soup.find_all(attrs={'itemprop': 'address'}):
        text = normalize_whitespace(tag.get_text(' ', strip=True))
        if text:
            candidates.append(text)
    for pattern in ('address', 'location', 'hq'):
        for tag in soup.find_all(lambda element: element.name in {'p', 'div', 'span'} and pattern in ' '.join(element.get('class', [])).lower()):
            text = normalize_whitespace(tag.get_text(' ', strip=True))
            if text:
                candidates.append(text)
    return dedupe_preserve_order(candidates)
