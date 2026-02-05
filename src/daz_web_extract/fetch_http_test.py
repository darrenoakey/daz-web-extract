import pytest

from daz_web_extract.fetch_http import fetch_http


# ##################################################################
# test fetch http success on example com
# example.com should return a successful result with title and body
@pytest.mark.asyncio
async def test_fetch_http_success_on_example_com():
    result = await fetch_http("https://example.com")
    assert result.success is True
    assert result.fetch_method == "httpx"
    assert result.status_code == 200
    assert result.title is not None
    assert "Example" in result.title
    assert result.body is not None
    assert len(result.body) >= 100
    assert result.content_length >= 100
    assert result.elapsed_ms > 0
    assert result.error is None


# ##################################################################
# test fetch http 404 returns failure
# a url that returns 404 should produce a failure result
@pytest.mark.asyncio
async def test_fetch_http_404_returns_failure():
    result = await fetch_http("https://httpbin.org/status/404")
    assert result.success is False
    assert result.fetch_method == "httpx"
    assert result.status_code == 404
    assert "404" in result.error


# ##################################################################
# test fetch http invalid domain returns failure
# a completely invalid domain should produce a connection error
@pytest.mark.asyncio
async def test_fetch_http_invalid_domain_returns_failure():
    result = await fetch_http("https://this-domain-absolutely-does-not-exist-xyz123.com")
    assert result.success is False
    assert result.fetch_method == "httpx"
    assert result.status_code is None
    assert result.error is not None
    assert result.elapsed_ms >= 0
