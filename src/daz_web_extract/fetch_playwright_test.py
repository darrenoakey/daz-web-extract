import pytest

from daz_web_extract.fetch_playwright import fetch_playwright, _dismiss_cookie_consent, COOKIE_CONSENT_SELECTORS


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


# ##################################################################
# test cookie consent selectors list is populated
# verify the selectors list covers common patterns
def test_cookie_consent_selectors_list_is_populated():
    assert len(COOKIE_CONSENT_SELECTORS) >= 10
    accept_selectors = [s for s in COOKIE_CONSENT_SELECTORS if "Accept" in s or "ACCEPT" in s]
    assert len(accept_selectors) >= 3


# ##################################################################
# test dismiss cookie consent on page without consent dialog
# should return without error on pages that have no cookie banner
@pytest.mark.asyncio
async def test_dismiss_cookie_consent_on_page_without_consent_dialog():
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto("https://example.com", wait_until="networkidle")
            await _dismiss_cookie_consent(page)
            html = await page.content()
            assert "Example" in html
        finally:
            await browser.close()
