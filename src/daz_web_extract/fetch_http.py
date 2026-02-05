from __future__ import annotations

import time

import httpx

from daz_web_extract.content import parse_html, extract_title, extract_body_text
from daz_web_extract.result import ExtractionResult, make_success, make_failure

TIMEOUT_SECONDS = 10
USER_AGENT = "Mozilla/5.0 (compatible; daz-web-extract/0.1)"


# ##################################################################
# fetch http
# tier 1: fast async httpx get with lxml heuristic extraction
async def fetch_http(url: str) -> ExtractionResult:
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = await client.get(url)
        elapsed = _elapsed_ms(start)
        if response.status_code >= 400:
            return make_failure(
                url=url,
                error=f"HTTP {response.status_code}",
                fetch_method="httpx",
                status_code=response.status_code,
                elapsed_ms=elapsed,
            )
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            return make_failure(
                url=url,
                error=f"Non-HTML content type: {content_type}",
                fetch_method="httpx",
                status_code=response.status_code,
                elapsed_ms=elapsed,
            )
        return _extract_from_html(url, response.content, response.status_code, elapsed)
    except Exception as err:
        elapsed = _elapsed_ms(start)
        return make_failure(
            url=url,
            error=f"{type(err).__name__}: {err}",
            fetch_method="httpx",
            status_code=None,
            elapsed_ms=elapsed,
        )


# ##################################################################
# extract from html
# parse html and extract title + body, returning a result
def _extract_from_html(url: str, html: bytes, status_code: int, elapsed_ms: int) -> ExtractionResult:
    tree = parse_html(html)
    title = extract_title(tree)
    body = extract_body_text(tree)
    if body is None or len(body) < 100:
        return make_failure(
            url=url,
            error="Body too short",
            fetch_method="httpx",
            status_code=status_code,
            elapsed_ms=elapsed_ms,
        )
    return make_success(
        url=url,
        title=title,
        body=body,
        fetch_method="httpx",
        status_code=status_code,
        elapsed_ms=elapsed_ms,
    )


# ##################################################################
# elapsed ms
# compute milliseconds since a monotonic start time
def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)
