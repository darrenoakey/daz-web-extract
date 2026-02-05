import pytest

from daz_web_extract.fetch_playwright import fetch_playwright


# ##################################################################
# test fetch playwright success on example com
# playwright should be able to render and extract from example.com
@pytest.mark.asyncio
async def test_fetch_playwright_success_on_example_com():
    result = await fetch_playwright("https://example.com")
    assert result.success is True
    assert result.fetch_method == "playwright"
    assert result.title is not None
    assert "Example" in result.title
    assert result.body is not None
    assert len(result.body) >= 100
    assert result.content_length >= 100
    assert result.elapsed_ms > 0
    assert result.error is None


# ##################################################################
# test fetch playwright invalid url returns failure
# an invalid domain should produce a failure result
@pytest.mark.asyncio
async def test_fetch_playwright_invalid_url_returns_failure():
    result = await fetch_playwright("https://this-domain-absolutely-does-not-exist-xyz123.com")
    assert result.success is False
    assert result.fetch_method == "playwright"
    assert result.elapsed_ms >= 0
    assert result.error is not None
