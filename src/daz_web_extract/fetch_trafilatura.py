from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import trafilatura

from daz_web_extract.result import ExtractionResult, make_success, make_failure

TIMEOUT_SECONDS = 15
_executor = ThreadPoolExecutor(max_workers=4)


# ##################################################################
# fetch trafilatura
# tier 2: use trafilatura to download and extract content via thread
# executor so it does not block the event loop
async def fetch_trafilatura(url: str) -> ExtractionResult:
    start = time.monotonic()
    loop = asyncio.get_running_loop()
    try:
        downloaded, extracted = await asyncio.wait_for(
            loop.run_in_executor(_executor, _download_and_extract, url),
            timeout=TIMEOUT_SECONDS,
        )
        elapsed = _elapsed_ms(start)
        if extracted is None or len(extracted) < 100:
            return make_failure(
                url=url,
                error="Body too short or extraction failed",
                fetch_method="trafilatura",
                status_code=None,
                elapsed_ms=elapsed,
            )
        title = _extract_title(downloaded)
        return make_success(
            url=url,
            title=title,
            body=extracted,
            fetch_method="trafilatura",
            status_code=None,
            elapsed_ms=elapsed,
        )
    except asyncio.TimeoutError:
        elapsed = _elapsed_ms(start)
        return make_failure(
            url=url,
            error="Trafilatura timeout",
            fetch_method="trafilatura",
            status_code=None,
            elapsed_ms=elapsed,
        )
    except Exception as err:
        elapsed = _elapsed_ms(start)
        return make_failure(
            url=url,
            error=f"{type(err).__name__}: {err}",
            fetch_method="trafilatura",
            status_code=None,
            elapsed_ms=elapsed,
        )


# ##################################################################
# download and extract
# synchronous trafilatura workflow: download html then extract text
def _download_and_extract(url: str) -> tuple[str | None, str | None]:
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return None, None
    extracted = trafilatura.extract(downloaded)
    return downloaded, extracted


# ##################################################################
# extract title
# pull title from downloaded html using trafilatura metadata
def _extract_title(downloaded: str | None) -> str | None:
    if downloaded is None:
        return None
    metadata = trafilatura.metadata.extract_metadata(downloaded)
    if metadata and metadata.title:
        return metadata.title
    return None


# ##################################################################
# elapsed ms
# compute milliseconds since a monotonic start time
def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)
