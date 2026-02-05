from daz_web_extract.content import parse_html, extract_title, extract_body_text


# ##################################################################
# test title from og tag
# og:title takes priority over all other title sources
def test_title_from_og_tag():
    html = """
    <html><head>
        <meta property="og:title" content="OG Title Here">
        <title>Page Title | SiteName</title>
    </head><body><h1>Heading</h1></body></html>
    """
    tree = parse_html(html)
    assert extract_title(tree) == "OG Title Here"


# ##################################################################
# test title from title tag with suffix cleaned
# title tag is used when og:title is missing, and site suffixes are removed
def test_title_from_title_tag_with_suffix_cleaned():
    html = """
    <html><head>
        <title>Article Title | SiteName</title>
    </head><body></body></html>
    """
    tree = parse_html(html)
    assert extract_title(tree) == "Article Title"


# ##################################################################
# test title from title tag dash suffix
# dash-style suffixes should also be cleaned
def test_title_from_title_tag_dash_suffix():
    html = """
    <html><head>
        <title>Article Title - SiteName</title>
    </head><body></body></html>
    """
    tree = parse_html(html)
    assert extract_title(tree) == "Article Title"


# ##################################################################
# test title from h1 fallback
# h1 is used as last resort when no og:title or title tag
def test_title_from_h1_fallback():
    html = """
    <html><head></head><body>
        <h1>Main Heading Text</h1>
    </body></html>
    """
    tree = parse_html(html)
    assert extract_title(tree) == "Main Heading Text"


# ##################################################################
# test title none when no title sources
# returns none when html has no title sources at all
def test_title_none_when_no_title_sources():
    html = "<html><head></head><body><p>Just a paragraph.</p></body></html>"
    tree = parse_html(html)
    assert extract_title(tree) is None


# ##################################################################
# test body extracts paragraphs
# body extraction collects text from p tags
def test_body_extracts_paragraphs():
    paragraphs = ["This is a paragraph with enough content to pass the filter."] * 5
    body_html = "".join(f"<p>{p}</p>" for p in paragraphs)
    html = f"<html><body>{body_html}</body></html>"
    tree = parse_html(html)
    body = extract_body_text(tree)
    assert body is not None
    for p in paragraphs:
        assert p in body


# ##################################################################
# test body removes noise elements
# script, style, nav, footer etc. should not appear in body
def test_body_removes_noise_elements():
    html = """
    <html><body>
        <script>var x = 1;</script>
        <style>.foo { color: red; }</style>
        <nav><a href="/">Home</a><a href="/about">About Us Page Link</a></nav>
        <footer>Copyright 2024 with long enough footer text to appear</footer>
        <p>This is the main article content that should be extracted properly from the page.</p>
        <p>Another paragraph of real content that has enough length to pass filtering.</p>
        <p>A third paragraph with substantial content that makes the body long enough overall.</p>
        <p>Fourth paragraph ensuring we have well over one hundred characters of body text here.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_body_text(tree)
    assert body is not None
    assert "var x = 1" not in body
    assert "color: red" not in body
    assert "This is the main article content" in body


# ##################################################################
# test body filters short blocks
# blocks shorter than 15 chars are dropped as likely menu items or labels
def test_body_filters_short_blocks():
    html = """
    <html><body>
        <p>OK</p>
        <p>This paragraph is long enough to be included in the body text extraction result.</p>
        <p>Hi</p>
        <p>Another long paragraph that exceeds the minimum block length requirement for inclusion.</p>
        <p>One more paragraph of sufficient length to ensure we pass the minimum body length check.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_body_text(tree)
    assert body is not None
    assert "OK" not in body
    assert "Hi" not in body
    assert "This paragraph is long enough" in body


# ##################################################################
# test body returns none for insufficient content
# body must be at least 100 chars total or returns none
def test_body_returns_none_for_insufficient_content():
    html = "<html><body><p>Short text.</p></body></html>"
    tree = parse_html(html)
    body = extract_body_text(tree)
    assert body is None


# ##################################################################
# test body collects headings
# h1-h6 are included as content blocks
def test_body_collects_headings():
    html = """
    <html><body>
        <h1>This is a main heading that is long enough to be included in the extraction results</h1>
        <h2>This subheading also has enough characters to pass the minimum block length filter</h2>
        <p>A paragraph with enough content to ensure the total body length meets the minimum requirement.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_body_text(tree)
    assert body is not None
    assert "This is a main heading" in body
    assert "This subheading also has" in body


# ##################################################################
# test body collects list items and blockquotes
# li and blockquote tags should be collected as content blocks
def test_body_collects_list_items_and_blockquotes():
    html = """
    <html><body>
        <ul>
            <li>This is a list item with enough text to be collected by the body extractor.</li>
            <li>Another list item that also has sufficient characters to pass the block filter.</li>
        </ul>
        <blockquote>This is a blockquote with enough content to be extracted as a body block.</blockquote>
        <p>Additional paragraph text to make sure the total body exceeds the minimum length threshold.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_body_text(tree)
    assert body is not None
    assert "This is a list item" in body
    assert "This is a blockquote" in body


# ##################################################################
# test parse html handles bytes
# parse_html should accept bytes input and decode properly
def test_parse_html_handles_bytes():
    html_bytes = b"<html><body><p>Hello from bytes content that is long enough to test.</p></body></html>"
    tree = parse_html(html_bytes)
    assert extract_title(tree) is None
