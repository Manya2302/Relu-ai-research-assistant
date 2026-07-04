from __future__ import annotations

IMPORTANT_PATHS = ('/', '/about', '/company', '/products', '/services', '/solutions', '/pricing', '/contact')
IGNORED_PATH_SEGMENTS = (
    'login',
    'signin',
    'sign-up',
    'signup',
    'register',
    'privacy',
    'terms',
    'careers',
    'jobs',
    'blog',
    'rss',
    'feed',
    'robots.txt',
    'sitemap',
    'cart',
    'checkout',
    'account',
    'admin',
)
BLOCKED_HOSTNAMES = {'localhost', '127.0.0.1', '0.0.0.0', '::1'}
COMPETITOR_LIMIT = 3
MODEL_LIMIT = 50
DEFAULT_RESEARCH_STAGES = (
    'Searching Company...',
    'Finding Official Website...',
    'Crawling Website...',
    'Extracting Content...',
    'Analyzing With AI...',
    'Generating PDF...',
    'Complete',
)

IMPORTANT_PATHS = ('/', '/about', '/company', '/products', '/services', '/solutions', '/pricing', '/contact')
IGNORED_PATH_SEGMENTS = (
    'login',
    'signin',
    'sign-up',
    'signup',
    'register',
    'privacy',
    'terms',
    'careers',
    'jobs',
    'blog',
    'rss',
    'feed',
    'robots.txt',
    'sitemap',
    'cart',
    'checkout',
    'account',
    'admin',
)
BLOCKED_HOSTNAMES = {'localhost', '127.0.0.1', '0.0.0.0', '::1'}
COMPETITOR_LIMIT = 3
MODEL_LIMIT = 50
DEFAULT_RESEARCH_STAGES = (
    'Searching Company...',
    'Finding Official Website...',
    'Crawling Website...',
    'Extracting Content...',
    'Analyzing With AI...',
    'Generating PDF...',
    'Complete',
)
SYSTEM_PROMPT = """You are a senior intelligence analyst. Extract precise facts from the provided context.
Return ONLY valid JSON matching the exact schema below. Do not include markdown formatting like ```json.

CRITICAL RULES:
1. NEVER confuse Revenue, Market Cap, Valuation, and Funding. They are distinct metrics. If a specific metric is not explicitly found, return an empty string. DO NOT use Market Cap as Revenue.
2. For subsidiaries or spin-offs, find the exact founder of that specific entity (e.g., F.C. Kohli for TCS), NOT the founder of the parent company (e.g. Jamsetji Tata).
3. Find highly specific domain competitors (e.g., niche peers like Cognizant, Capgemini, or LTTS for engineering/IT), not just generic IT giants. Provide at least 5 if possible.
4. Extract up to 10 major products, platforms, or service lines. Do not limit to just 1-2.
4. Make the summary and pain_points hyper-specific to the exact niche, products, and engineering verticals of the company. Avoid generic business jargon.
5. If data is unavailable, return an empty string "". DO NOT return "Not available" or "N/A" or "Unknown".

SCHEMA:
{
  "company_name": "Exact company name",
  "summary": "Specific 2-3 sentence overview of their core business model, target industry, and unique value proposition.",
  "website": "Primary URL",
  "phone": "Main contact number",
  "address": "Headquarters address (Physical address, NOT a URL or web portal)",
  "revenue": "Annual revenue with currency and year (e.g., $1.2B (2023))",
  "market_cap": "Market capitalization (if applicable)",
  "funding": "Total funding or latest round (if applicable)",
  "industry": "Primary industry",
  "country": "HQ country",
  "leadership_info": {
    "ceo": "CEO Name",
    "cfo": "CFO Name",
    "cto": "CTO Name",
    "founders": ["Founder 1", "Founder 2"],
    "board_members": ["Board Member 1"]
  },
  "products": ["Specific Product/Platform/Service 1", "Product 2 (Max 10)"],
  "pain_points": ["Specific industry challenge 1", "Specific risk 2 (Max 5)"],
  "recommendations": ["Actionable next step 1 (e.g. Monitor EV contracts)", "Actionable next step 2 (Max 4)"],
  "competitors": [
    {
      "name": "Direct Competitor Name",
      "website": "URL if known",
      "reason": "Why they compete in this specific niche"
    }
  ]
}"""
