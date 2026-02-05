import asyncio
import json

import pytest

from daz_web_extract.extract import extract


# ##################################################################
# test extract full pipeline success
# extract should successfully return content from example.com
@pytest.mark.asyncio
async def test_extract_full_pipeline_success():
    result = await extract("https://example.com")
    assert result.success is True
    assert result.url == "https://example.com"
    assert result.title is not None
    assert result.body is not None
    assert result.content_length >= 100
    assert result.fetch_method in {"httpx", "trafilatura", "playwright"}
    assert result.error is None


# ##################################################################
# test extract invalid url failure
# a completely invalid url should return a failure result
@pytest.mark.asyncio
async def test_extract_invalid_url_failure():
    result = await extract("https://this-domain-absolutely-does-not-exist-xyz123.com")
    assert result.success is False
    assert result.error is not None
    assert result.url == "https://this-domain-absolutely-does-not-exist-xyz123.com"


# ##################################################################
# test extract concurrent gather
# five concurrent extractions should all complete without errors
@pytest.mark.asyncio
async def test_extract_concurrent_gather():
    urls = [
        "https://example.com",
        "https://www.iana.org/help/example-domains",
        "https://example.org",
        "https://www.iana.org/about",
        "https://www.iana.org/performance/ietf-statistics",
    ]
    results = await asyncio.gather(*(extract(u) for u in urls))
    assert len(results) == 5
    for result in results:
        assert result.url in urls
        assert result.elapsed_ms >= 0


# ##################################################################
# test extract max tier 1 respects limit
# max_tier=1 should only use httpx, never escalate
@pytest.mark.asyncio
async def test_extract_max_tier_1_respects_limit():
    result = await extract("https://example.com", max_tier=1)
    assert result.fetch_method == "httpx"


# ##################################################################
# test extract elapsed ms positive
# elapsed time should always be greater than zero
@pytest.mark.asyncio
async def test_extract_elapsed_ms_positive():
    result = await extract("https://example.com")
    assert result.elapsed_ms > 0


# ##################################################################
# test extract json serializable
# the result should be json serializable without errors
@pytest.mark.asyncio
async def test_extract_json_serializable():
    result = await extract("https://example.com")
    j = result.to_json()
    parsed = json.loads(j)
    assert isinstance(parsed, dict)
    assert parsed["url"] == "https://example.com"
    assert isinstance(parsed["success"], bool)
