from __future__ import annotations

import re

import lxml.html


NOISE_TAGS = {
    "script", "style", "nav", "footer", "aside", "header", "noscript",
    "iframe", "form", "svg", "button", "select", "option", "textarea",
    "input", "label", "fieldset", "legend", "dialog", "menu", "menuitem",
    "details", "summary",
}
NOISE_CLASSES = {
    "ad", "ads", "advert", "advertisement", "banner", "sponsor", "sponsored",
    "promo", "promotion", "sidebar", "widget", "social", "share", "sharing",
    "cookie", "consent", "popup", "modal", "overlay", "newsletter",
    "subscribe", "signup", "sign-up", "cta", "call-to-action",
    "related", "recommended", "trending", "popular", "breadcrumb",
    "pagination", "pager", "toolbar", "tooltip", "dropdown",
    "comment", "comments", "disqus",
}
NOISE_IDS = {
    "ad", "ads", "sidebar", "cookie-banner", "newsletter",
    "comments", "disqus_thread", "social-share",
}
NOISE_ROLES = {"navigation", "banner", "complementary", "contentinfo", "form", "search", "menu", "menubar"}
CONTENT_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "td", "th", "figcaption", "pre", "dd"}
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
# extract text content
# pull clean article text from html by collecting text from content
# tags after removing all noise elements; link text is preserved but
# all html formatting is stripped to produce plain text
def extract_text_content(tree: lxml.html.HtmlElement) -> str | None:
    _remove_noise(tree)
    blocks = _collect_blocks(tree)
    filtered = [b for b in blocks if len(b) >= MIN_BLOCK_LENGTH]
    body = "\n\n".join(filtered)
    if len(body) < MIN_BODY_LENGTH:
        return None
    return body


# ##################################################################
# remove noise
# strip script, style, nav, footer, ads, forms, and other noise
# elements from tree using tags, class names, ids, and aria roles
def _remove_noise(tree: lxml.html.HtmlElement) -> None:
    to_remove = []
    for el in tree.xpath("//*"):
        if _is_noise_element(el):
            to_remove.append(el)
    for el in to_remove:
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)


# ##################################################################
# is noise element
# check whether an element is noise by tag, class, id, or role
def _is_noise_element(el: lxml.html.HtmlElement) -> bool:
    if el.tag in NOISE_TAGS:
        return True
    classes = set(el.get("class", "").lower().split())
    if classes & NOISE_CLASSES:
        return True
    el_id = el.get("id", "").lower()
    if el_id in NOISE_IDS:
        return True
    role = el.get("role", "").lower()
    if role in NOISE_ROLES:
        return True
    return False


# ##################################################################
# collect blocks
# gather text content from paragraph-like elements; link text within
# paragraphs is preserved since links are part of article content
def _collect_blocks(tree: lxml.html.HtmlElement) -> list[str]:
    blocks: list[str] = []
    for el in tree.xpath("//*"):
        if el.tag in CONTENT_TAGS:
            text = el.text_content().strip()
            text = re.sub(r"\s+", " ", text)
            if text:
                blocks.append(text)
    return blocks
