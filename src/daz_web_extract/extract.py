from __future__ import annotations

import time

from daz_web_extract.result import ExtractionResult, make_failure
from daz_web_extract.fetch_http import fetch_http
from daz_web_extract.fetch_trafilatura import fetch_trafilatura
from daz_web_extract.fetch_playwright import fetch_playwright

SKIP_TO_TIER3_CODES = set(range(400, 600)) - {403, 429}


# ##################################################################
# extract
# public api: extract clean title and body text from a url using
# a three-tier fetch strategy (httpx -> trafilatura -> playwright).
# never throws; always returns ExtractionResult with success or failure.
async def extract(url: str, max_tier: int = 3) -> ExtractionResult:
    start = time.monotonic()

    tier1_result = await fetch_http(url)
    if tier1_result.success:
        return tier1_result

    if max_tier < 2:
        return tier1_result

    if _should_skip_to_tier3(tier1_result) and max_tier >= 3:
        return await _run_tier3(url, start)

    tier2_result = await fetch_trafilatura(url)
    if tier2_result.success:
        return tier2_result

    if max_tier < 3:
        return tier2_result

    return await _run_tier3(url, start)


# ##################################################################
# should skip to tier3
# http 4xx/5xx (except 403 and 429) skip tier 2 and go straight to
# playwright because the server explicitly rejected the request
def _should_skip_to_tier3(result: ExtractionResult) -> bool:
    if result.status_code is not None and result.status_code in SKIP_TO_TIER3_CODES:
        return True
    return False


# ##################################################################
# run tier3
# run playwright extraction as final tier
async def _run_tier3(url: str, overall_start: float) -> ExtractionResult:
    result = await fetch_playwright(url)
    if result.success:
        return result
    elapsed = int((time.monotonic() - overall_start) * 1000)
    return make_failure(
        url=url,
        error=f"All tiers failed: {result.error}",
        fetch_method="playwright",
        status_code=result.status_code,
        elapsed_ms=elapsed,
    )
