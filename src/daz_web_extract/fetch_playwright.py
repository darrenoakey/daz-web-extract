from __future__ import annotations

import asyncio
import time

from playwright.async_api import async_playwright

from daz_web_extract.content import parse_html, extract_title, extract_text_content
from daz_web_extract.result import ExtractionResult, make_success, make_failure

TIMEOUT_MS = 30000
_browser_semaphore = asyncio.Semaphore(3)


# ##################################################################
# fetch playwright
# tier 3: headless chromium browser for javascript-rendered pages;
# semaphore limits to 3 concurrent browser instances
async def fetch_playwright(url: str) -> ExtractionResult:
    start = time.monotonic()
    async with _browser_semaphore:
        try:
            return await _fetch_with_browser(url, start)
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
# fetch with browser
# launch browser, navigate, extract content, close browser
async def _fetch_with_browser(url: str, start: float) -> ExtractionResult:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            response = await page.goto(url, wait_until="networkidle", timeout=TIMEOUT_MS)
            status_code = response.status if response else None
            if status_code and status_code >= 400:
                elapsed = _elapsed_ms(start)
                return make_failure(
                    url=url,
                    error=f"HTTP {status_code}",
                    fetch_method="playwright",
                    status_code=status_code,
                    elapsed_ms=elapsed,
                )
            html = await page.content()
            elapsed = _elapsed_ms(start)
            return _extract_from_html(url, html, status_code, elapsed)
        finally:
            await browser.close()


# ##################################################################
# extract from html
# try trafilatura first, fall back to lxml heuristic
def _extract_from_html(url: str, html: str, status_code: int | None, elapsed_ms: int) -> ExtractionResult:
    body = _try_trafilatura(html)
    if body is None or len(body) < 100:
        body = _try_lxml(html)
    if body is None or len(body) < 100:
        return make_failure(
            url=url,
            error="Body too short",
            fetch_method="playwright",
            status_code=status_code,
            elapsed_ms=elapsed_ms,
        )
    tree = parse_html(html)
    title = extract_title(tree)
    return make_success(
        url=url,
        title=title,
        body=body,
        fetch_method="playwright",
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
