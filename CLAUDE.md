# daz-web-extract

Async Python library that extracts clean title + body text from any URL using a three-tier fetch strategy.

## Architecture

Three-tier escalation: httpx (fast, 10s) -> trafilatura (thread executor, 15s) -> playwright (headless browser, 30s).
Never throws exceptions - always returns `ExtractionResult` with `success=True|False`.

### Skip Logic
HTTP 4xx/5xx (except 403/429) skip tier 2 and go straight to playwright.
`max_tier` param caps which tiers are tried (1=httpx only, 2=httpx+trafilatura, 3=all).

### Concurrency
- Tier 1: fully async-native via httpx
- Tier 2: `run_in_executor` with `asyncio.wait_for` timeout
- Tier 3: `asyncio.Semaphore(3)` limits concurrent browser instances

## Key Files

- `src/daz_web_extract/result.py` - ExtractionResult frozen dataclass + make_success/make_failure
- `src/daz_web_extract/content.py` - lxml heuristic: `extract_title` (og:title > title > h1), `extract_text_content` (noise removal + block filtering)
- `src/daz_web_extract/fetch_http.py` - Tier 1: async httpx
- `src/daz_web_extract/fetch_trafilatura.py` - Tier 2: trafilatura via thread executor
- `src/daz_web_extract/fetch_playwright.py` - Tier 3: playwright headless chromium
- `src/daz_web_extract/extract.py` - Orchestrator with skip logic
- `run` - CLI facade: test, lint, check, extract, publish, verify (no separate run_cli.py)

## Commands (via `./run`)

- `./run test <path>` - Run a single test target
- `./run lint` - Run ruff linter
- `./run check` - Run dazpycheck full quality gate
- `./run extract <url> [--raw]` - Extract content from a URL
- `./run publish` - Build and upload to PyPI (requires keychain access, run from real terminal)
- `./run verify` - Lint + full test suite (used by pre-commit hooks)

## Testing

89 tests total (70 content extraction tests with crafted HTML, 19 integration tests hitting example.com, httpbin.org, iana.org).
pytest-asyncio with `asyncio_mode = "auto"`.

## Gotchas

- pyproject.toml build-backend must be `setuptools.build_meta` (not `setuptools.backends._legacy:_Backend`)
- Playwright chromium must be installed separately: `.venv/bin/playwright install chromium`
- trafilatura metadata API: `trafilatura.metadata.extract_metadata(html)` returns a `Document` object with `.title`
- Content body requires >= 100 chars, individual blocks >= 15 chars
- Noise filtering uses tags, CSS classes, element IDs, and ARIA roles (not just tags)
- The function is `extract_text_content` (not `extract_body_text`) - named for article text extraction vs future site-driving extractions
- Link text within paragraphs is preserved (links are part of article content); all HTML formatting is stripped
