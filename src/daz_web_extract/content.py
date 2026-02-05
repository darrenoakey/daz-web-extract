from __future__ import annotations

import re

import lxml.html


NOISE_TAGS = {"script", "style", "nav", "footer", "aside", "header", "noscript", "iframe", "form", "svg"}
CONTENT_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "td"}
MIN_BLOCK_LENGTH = 15
MIN_BODY_LENGTH = 100
TITLE_SUFFIX_RE = re.compile(r"\s*[\|\-\u2013\u2014]\s*[^|\-\u2013\u2014]+$")


# ##################################################################
# parse html
# convert raw html bytes or string into an lxml element tree
def parse_html(html: str | bytes) -> lxml.html.HtmlElement:
    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="replace")
    return lxml.html.fromstring(html)


# ##################################################################
# extract title
# pull the best title from html using priority: og:title > <title> > first h1
def extract_title(tree: lxml.html.HtmlElement) -> str | None:
    og = tree.xpath('//meta[@property="og:title"]/@content')
    if og and og[0].strip():
        return og[0].strip()

    title_els = tree.xpath("//title/text()")
    if title_els:
        raw = title_els[0].strip()
        if raw:
            return _clean_title_suffix(raw)

    h1_els = tree.xpath("//h1//text()")
    if h1_els:
        combined = " ".join(t.strip() for t in h1_els if t.strip())
        if combined:
            return combined

    return None


# ##################################################################
# clean title suffix
# remove common site name suffixes like " | SiteName" or " - SiteName"
def _clean_title_suffix(title: str) -> str:
    cleaned = TITLE_SUFFIX_RE.sub("", title)
    return cleaned if cleaned.strip() else title


# ##################################################################
# extract body text
# pull clean body text from html by collecting text from content tags
# after removing noise elements
def extract_body_text(tree: lxml.html.HtmlElement) -> str | None:
    _remove_noise(tree)
    blocks = _collect_blocks(tree)
    filtered = [b for b in blocks if len(b) >= MIN_BLOCK_LENGTH]
    body = "\n\n".join(filtered)
    if len(body) < MIN_BODY_LENGTH:
        return None
    return body


# ##################################################################
# remove noise
# strip script, style, nav, footer, and other noise elements from tree
def _remove_noise(tree: lxml.html.HtmlElement) -> None:
    for el in tree.xpath("//*"):
        if el.tag in NOISE_TAGS:
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)


# ##################################################################
# collect blocks
# gather text content from paragraph-like elements
def _collect_blocks(tree: lxml.html.HtmlElement) -> list[str]:
    blocks: list[str] = []
    for el in tree.xpath("//*"):
        if el.tag in CONTENT_TAGS:
            text = el.text_content().strip()
            text = re.sub(r"\s+", " ", text)
            if text:
                blocks.append(text)
    return blocks
