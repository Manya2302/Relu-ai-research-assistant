# Website Crawling Implementation

The Relu AI Website Crawler (`backend/app/services/crawler_service.py`) is designed to rapidly and intelligently extract meaningful text from corporate websites without overwhelming the target server.

## Architecture & Flow

1. **Intelligent Page Discovery**
   When provided a base URL, the crawler fetches the homepage and parses the DOM using `BeautifulSoup`. It scans all `<a>` tags and identifies internal links. 

2. **Heuristic Filtering**
   To prevent wasting time on irrelevant pages, the crawler runs URLs through an exclusion list (`IGNORED_PATH_SEGMENTS`). It explicitly skips pages containing:
   - `login`, `signup`, `register`
   - `privacy`, `terms`
   - `cart`, `checkout`
   - Assets like `.pdf`, `.jpg`, `.mp4`

3. **Concurrent Processing**
   Once a queue of valuable pages (like `/about`, `/services`, `/contact`) is built, the crawler uses `asyncio.gather` combined with `httpx.AsyncClient`. It fetches up to 8 pages simultaneously, drastically reducing the crawl time from minutes to seconds.

4. **Duplicate Detection**
   The crawler maintains a strict `seen_urls` set. Before fetching any page, it normalizes the URL (stripping out marketing tracking parameters like `utm_source` and `gclid`) to ensure that `example.com/about?ref=twitter` and `example.com/about` are correctly treated as the exact same page.

5. **Content Extraction & Cleaning**
   The raw HTML of modern websites is flooded with React/Angular boilerplate, inline CSS, and tracker scripts. 
   - The crawler strips all `<script>`, `<style>`, `<nav>`, and `<footer>` tags.
   - It targets specific, high-signal tags: `<h1>`, `<h2>`, `<h3>`, and `<p>`.
   - The final output is a clean, structured payload of plain text, completely optimized for LLM context windows.
