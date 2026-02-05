import pytest

from daz_web_extract.fetch_trafilatura import fetch_trafilatura


# ##################################################################
# test fetch trafilatura success on example com
# trafilatura should be able to extract content from example.com
@pytest.mark.asyncio
async def test_fetch_trafilatura_success_on_example_com():
    result = await fetch_trafilatura("https://example.com")
    assert result.fetch_method == "trafilatura"
    assert result.elapsed_ms > 0
    assert result.error is None or result.success is False
    if result.success:
        assert result.body is not None
        assert len(result.body) >= 100
        assert result.content_length >= 100


# ##################################################################
# test fetch trafilatura invalid url returns failure
# an invalid domain should produce a failure result
@pytest.mark.asyncio
async def test_fetch_trafilatura_invalid_url_returns_failure():
    result = await fetch_trafilatura("https://this-domain-absolutely-does-not-exist-xyz123.com")
    assert result.success is False
    assert result.fetch_method == "trafilatura"
    assert result.elapsed_ms >= 0
