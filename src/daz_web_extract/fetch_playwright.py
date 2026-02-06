from __future__ import annotations

import asyncio
import time

from playwright.async_api import async_playwright

from daz_web_extract.content import parse_html, extract_title, extract_text_content
from daz_web_extract.result import ExtractionResult, make_success, make_failure

TIMEOUT_MS = 30000
_browser_semaphore = asyncio.Semaphore(3)
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

COOKIE_CONSENT_SELECTORS = [
    'button:has-text("ACCEPT")',
    'button:has-text("Accept All")',
    'button:has-text("Accept all")',
    'button:has-text("Accept")',
    '#onetrust-accept-btn-handler',
    '.accept-cookies',
    'button:has-text("I agree")',
    'button:has-text("Allow all")',
    'button:has-text("OK")',
    'button:has-text("Got it")',
    'button:has-text("Agree")',
    '[data-testid="cookie-accept"]',
    'button:has-text("Continue")',
]

_JS_REQUIRED_PHRASES = [
    "requires javascript",
    "enable javascript",
    "javascript is required",
    "javascript is disabled",
    "javascript must be enabled",
    "you need to enable javascript",
    "please enable javascript",
    "this site requires javascript",
    "this page requires javascript",
    "this application requires javascript",
    "browser does not support javascript",
    "turn on javascript",
    "activate javascript",
]


# ##################################################################
# fetch playwright nojs
# tier 3: headless chromium with JS disabled; fast SSR extraction
# that avoids hydration failures on server-rendered sites
async def fetch_playwright_nojs(url: str) -> ExtractionResult:
    start = time.monotonic()
    async with _browser_semaphore:
        try:
            return await _fetch_page(url, start, js_enabled=False)
        except Exception as err:
            elapsed = _elapsed_ms(start)
            return make_failure(
                url=url,
                error=f"{type(err).__name__}: {err}",
                fetch_method="playwright-nojs",
                status_code=None,
                elapsed_ms=elapsed,
            )


# ##################################################################
# fetch playwright
# tier 4: headless chromium with JS enabled; full browser for SPAs
# and pages that require client-side rendering
async def fetch_playwright(url: str) -> ExtractionResult:
    start = time.monotonic()
    async with _browser_semaphore:
        try:
            return await _fetch_page(url, start, js_enabled=True)
        except Exception as err:
            elapsed = _elapsed_ms(start)
            return make_failure(
                url=url,
                error=f"{type(err).__name__}: {err}",
                fetch_method="playwright",
                status_code=None,
                elapsed_ms=elapsed,
            )


# ##################################################################
# requires javascript
# check if extracted body text indicates the page needs JS to render
def requires_javascript(result: ExtractionResult) -> bool:
    if not result.body:
        return False
    lower = result.body.lower()
    return any(phrase in lower for phrase in _JS_REQUIRED_PHRASES)


# ##################################################################
# dismiss cookie consent
# try common cookie consent button selectors; click the first one found
async def _dismiss_cookie_consent(page) -> None:
    for selector in COOKIE_CONSENT_SELECTORS:
        try:
            button = page.locator(selector).first
            if await button.is_visible(timeout=500):
                await button.click()
                await page.wait_for_load_state("networkidle", timeout=5000)
                return
        except Exception:
            continue


# ##################################################################
# fetch page
# shared implementation for both JS-enabled and JS-disabled modes
async def _fetch_page(url: str, start: float, *, js_enabled: bool) -> ExtractionResult:
    method = "playwright" if js_enabled else "playwright-nojs"
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            ctx = await browser.new_context(
                user_agent=_USER_AGENT,
                java_script_enabled=js_enabled,
            )
            try:
                page = await ctx.new_page()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
                if js_enabled:
                    # Best-effort wait for JS to finish rendering; proceed if network never settles
                    # (sites like openai.com keep websockets/analytics alive indefinitely)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                status_code = response.status if response else None
                if status_code and status_code >= 400:
                    elapsed = _elapsed_ms(start)
                    return make_failure(
                        url=url,
                        error=f"HTTP {status_code}",
                        fetch_method=method,
                        status_code=status_code,
                        elapsed_ms=elapsed,
                    )
                if js_enabled:
                    await _dismiss_cookie_consent(page)
                html = await page.content()
                elapsed = _elapsed_ms(start)
                return _extract_from_html(url, html, status_code, elapsed, method)
            finally:
                await ctx.close()
        finally:
            await browser.close()


# ##################################################################
# extract from html
# try trafilatura first, fall back to lxml heuristic
def _extract_from_html(
    url: str, html: str, status_code: int | None, elapsed_ms: int, method: str,
) -> ExtractionResult:
    body = _try_trafilatura(html)
    if body is None or len(body) < 100:
        body = _try_lxml(html)
    if body is None or len(body) < 100:
        return make_failure(
            url=url,
            error="Body too short",
            fetch_method=method,
            status_code=status_code,
            elapsed_ms=elapsed_ms,
        )
    tree = parse_html(html)
    title = extract_title(tree)
    return make_success(
        url=url,
        title=title,
        body=body,
        fetch_method=method,
        status_code=status_code,
        elapsed_ms=elapsed_ms,
    )


# ##################################################################
# try trafilatura
# attempt extraction using trafilatura on the rendered html string
def _try_trafilatura(html: str) -> str | None:
    try:
        import trafilatura
        return trafilatura.extract(html)
    except Exception:
        return None


# ##################################################################
# try lxml
# fall back to lxml heuristic extraction
def _try_lxml(html: str) -> str | None:
    try:
        tree = parse_html(html)
        return extract_text_content(tree)
    except Exception:
        return None


# ##################################################################
# elapsed ms
# compute milliseconds since a monotonic start time
def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)
