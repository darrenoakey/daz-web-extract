from daz_web_extract.content import parse_html, extract_title, extract_text_content


ARTICLE_BODY = """
<p>The global economy showed signs of recovery in the third quarter, with major indices
rising across all sectors. Analysts at Goldman Sachs noted that consumer spending has
returned to pre-pandemic levels in most developed nations.</p>
<p>Technology stocks led the rally, with the NASDAQ composite gaining twelve percent over
the previous quarter. The gains were driven by strong earnings reports from major cloud
computing providers and semiconductor manufacturers.</p>
<p>Meanwhile, the European Central Bank held interest rates steady at its latest meeting,
citing concerns about persistent inflation in the services sector. The decision was widely
expected by market participants who had been monitoring recent economic data closely.</p>
<p>In related news, the housing market continues to cool after two years of rapid price
appreciation. Mortgage applications have fallen for the sixth consecutive week as buyers
adjust to the higher interest rate environment that has prevailed since mid-year.</p>
"""


# ##################################################################
# wrap article
# helper to wrap article paragraphs with arbitrary surrounding noise
def _wrap_article(noise_before: str = "", noise_after: str = "") -> str:
    return f"<html><body>{noise_before}<article>{ARTICLE_BODY}</article>{noise_after}</body></html>"


# ===================================================================
# TITLE TESTS
# ===================================================================


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


# ===================================================================
# BASIC CONTENT EXTRACTION TESTS
# ===================================================================


# ##################################################################
# test body extracts paragraphs
# body extraction collects text from p tags
def test_body_extracts_paragraphs():
    paragraphs = ["This is a paragraph with enough content to pass the filter."] * 5
    body_html = "".join(f"<p>{p}</p>" for p in paragraphs)
    html = f"<html><body>{body_html}</body></html>"
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    for p in paragraphs:
        assert p in body


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
    body = extract_text_content(tree)
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
    body = extract_text_content(tree)
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
    body = extract_text_content(tree)
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
    body = extract_text_content(tree)
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


# ===================================================================
# NAVIGATION NOISE TESTS
# ===================================================================


# ##################################################################
# test strips nav tag
# nav element and all its children should be completely removed
def test_strips_nav_tag():
    nav = """
    <nav>
        <a href="/">Home</a>
        <a href="/news">News</a>
        <a href="/sport">Sport</a>
        <a href="/weather">Weather</a>
        <a href="/business">Business</a>
    </nav>
    """
    tree = parse_html(_wrap_article(noise_before=nav))
    body = extract_text_content(tree)
    assert body is not None
    assert "Home" not in body
    assert "Sport" not in body
    assert "Weather" not in body
    assert "global economy" in body


# ##################################################################
# test strips hamburger menu nav
# mobile hamburger menus with nested ul/li inside nav should be stripped
def test_strips_hamburger_menu_nav():
    nav = """
    <nav class="mobile-nav" id="hamburger-menu">
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/about">About Us</a></li>
            <li><a href="/contact">Contact</a></li>
            <li><a href="/careers">Careers</a></li>
            <li><a href="/advertise">Advertise With Us</a></li>
        </ul>
    </nav>
    """
    tree = parse_html(_wrap_article(noise_before=nav))
    body = extract_text_content(tree)
    assert body is not None
    assert "Careers" not in body
    assert "Advertise With Us" not in body


# ##################################################################
# test strips header with logo and nav
# site header with branding and navigation links should be stripped
def test_strips_header_with_logo_and_nav():
    header = """
    <header>
        <div class="logo"><a href="/">NewsDaily</a></div>
        <nav>
            <a href="/politics">Politics</a>
            <a href="/tech">Technology</a>
            <a href="/culture">Culture</a>
        </nav>
        <div class="search"><input type="text" placeholder="Search..."></div>
    </header>
    """
    tree = parse_html(_wrap_article(noise_before=header))
    body = extract_text_content(tree)
    assert body is not None
    assert "NewsDaily" not in body
    assert "Politics" not in body
    assert "Technology" not in body.split("Technology stocks")[0] if "Technology stocks" in body else True


# ##################################################################
# test strips breadcrumb navigation
# breadcrumb trails should not appear in extracted text
def test_strips_breadcrumb_navigation():
    breadcrumb = """
    <div class="breadcrumb">
        <a href="/">Home</a> &gt; <a href="/news">News</a> &gt;
        <a href="/news/business">Business</a> &gt; <span>Market Report</span>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=breadcrumb))
    body = extract_text_content(tree)
    assert body is not None
    assert "Home" not in body


# ##################################################################
# test strips navigation role
# elements with role=navigation should be stripped
def test_strips_navigation_role():
    nav = """
    <div role="navigation" aria-label="Main">
        <a href="/section1">Section One Navigation Link</a>
        <a href="/section2">Section Two Navigation Link</a>
        <a href="/section3">Section Three Navigation Link</a>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=nav))
    body = extract_text_content(tree)
    assert body is not None
    assert "Section One Navigation Link" not in body


# ##################################################################
# test strips pagination
# pagination links for multi-page articles should not appear
def test_strips_pagination():
    pagination = """
    <div class="pagination">
        <a href="?page=1">1</a>
        <a href="?page=2">2</a>
        <a href="?page=3">3</a>
        <a href="?page=4">Next Page</a>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=pagination))
    body = extract_text_content(tree)
    assert body is not None
    assert "Next Page" not in body


# ===================================================================
# ADVERTISING NOISE TESTS
# ===================================================================


# ##################################################################
# test strips ad class div
# divs with class "ad" or "advertisement" should be fully removed
def test_strips_ad_class_div():
    ad = """
    <div class="ad">
        <p>Special offer! Buy one get one free on all premium subscriptions today only.</p>
        <a href="/subscribe">Subscribe Now for Half Price</a>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=ad))
    body = extract_text_content(tree)
    assert body is not None
    assert "Special offer" not in body
    assert "Subscribe Now" not in body


# ##################################################################
# test strips advertisement class
# elements with class "advertisement" should be stripped
def test_strips_advertisement_class():
    ad = """
    <div class="advertisement">
        <img src="ad-banner.jpg" alt="Amazing deals">
        <p>Click here for amazing deals on electronics and home appliances this holiday season.</p>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=ad))
    body = extract_text_content(tree)
    assert body is not None
    assert "amazing deals" not in body


# ##################################################################
# test strips sponsored content
# elements with class "sponsored" or "sponsor" should be stripped
def test_strips_sponsored_content():
    sponsored = """
    <div class="sponsored">
        <p>Sponsored: Discover the new range of luxury watches from SwissTime. Premium
        craftsmanship meets modern design in our latest collection available worldwide.</p>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=sponsored))
    body = extract_text_content(tree)
    assert body is not None
    assert "SwissTime" not in body
    assert "luxury watches" not in body


# ##################################################################
# test strips banner class
# elements with class "banner" should be stripped
def test_strips_banner_class():
    banner = """
    <div class="banner">
        <h2>Breaking: Subscribe to our premium newsletter for exclusive market analysis</h2>
        <a href="/subscribe">Get Premium Access Today</a>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=banner))
    body = extract_text_content(tree)
    assert body is not None
    assert "exclusive market analysis" not in body


# ##################################################################
# test strips promo class
# elements with class "promo" or "promotion" should be stripped
def test_strips_promo_class():
    promo = """
    <div class="promo">
        <p>Limited time promotion: Get fifty percent off your first year of digital access.</p>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=promo))
    body = extract_text_content(tree)
    assert body is not None
    assert "fifty percent off" not in body


# ##################################################################
# test strips inline ad between paragraphs
# ads injected between article paragraphs should be removed
def test_strips_inline_ad_between_paragraphs():
    html = """
    <html><body>
        <p>The government announced new regulations for the technology sector today. The rules
        will affect how companies handle personal data and require stricter compliance measures.</p>
        <div class="ad">
            <p>Try our new app! Download now and get a free trial for thirty days.</p>
        </div>
        <p>Industry leaders responded with mixed reactions. Some praised the clarity of the new
        framework while others expressed concern about implementation costs for smaller firms.</p>
        <div class="advertisement">
            <p>Best deals on laptops this week! Save up to forty percent on selected models.</p>
        </div>
        <p>The regulations are expected to take effect in the first quarter of next year, giving
        companies approximately six months to prepare their systems and processes for compliance.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "free trial" not in body
    assert "Best deals on laptops" not in body
    assert "new regulations" in body
    assert "mixed reactions" in body
    assert "take effect" in body


# ##################################################################
# test strips multiple ad class variations
# different naming conventions for ad classes should all be caught
def test_strips_multiple_ad_class_variations():
    noise = """
    <div class="ads"><p>Premium content sponsor message with enough text to be visible.</p></div>
    <div class="advert"><p>Check out these amazing products from our advertising partners now.</p></div>
    <div class="sponsor"><p>This article is brought to you by CloudHost enterprise solutions.</p></div>
    """
    tree = parse_html(_wrap_article(noise_before=noise))
    body = extract_text_content(tree)
    assert body is not None
    assert "sponsor message" not in body
    assert "advertising partners" not in body
    assert "CloudHost" not in body


# ===================================================================
# FORM NOISE TESTS
# ===================================================================


# ##################################################################
# test strips form elements
# forms with inputs, textareas, buttons, and selects should be stripped
def test_strips_form_elements():
    form = """
    <form action="/search" method="get">
        <label for="query">Search the site:</label>
        <input type="text" id="query" name="q" placeholder="Enter search terms">
        <button type="submit">Search</button>
    </form>
    """
    tree = parse_html(_wrap_article(noise_before=form))
    body = extract_text_content(tree)
    assert body is not None
    assert "Search the site" not in body
    assert "Enter search terms" not in body


# ##################################################################
# test strips login form
# login and authentication forms should not appear in article text
def test_strips_login_form():
    form = """
    <form class="login-form" action="/auth/login" method="post">
        <h3>Sign in to your account</h3>
        <label>Email address</label>
        <input type="email" name="email">
        <label>Password</label>
        <input type="password" name="password">
        <button type="submit">Sign In</button>
        <a href="/forgot-password">Forgot your password?</a>
    </form>
    """
    tree = parse_html(_wrap_article(noise_before=form))
    body = extract_text_content(tree)
    assert body is not None
    assert "Sign in to your account" not in body
    assert "Email address" not in body
    assert "Forgot your password" not in body


# ##################################################################
# test strips newsletter signup form
# newsletter subscription forms should be stripped
def test_strips_newsletter_signup_form():
    newsletter = """
    <div class="newsletter">
        <h3>Stay informed with our daily newsletter</h3>
        <p>Get the latest news delivered straight to your inbox every morning.</p>
        <form action="/subscribe">
            <input type="email" placeholder="your@email.com">
            <button>Subscribe Now</button>
        </form>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=newsletter))
    body = extract_text_content(tree)
    assert body is not None
    assert "daily newsletter" not in body
    assert "Subscribe Now" not in body
    assert "delivered straight" not in body


# ##################################################################
# test strips contact form
# contact forms with multiple fields and textareas should be removed
def test_strips_contact_form():
    form = """
    <form class="contact-form" action="/contact" method="post">
        <label for="name">Your Name</label>
        <input type="text" id="name" name="name">
        <label for="email">Your Email</label>
        <input type="email" id="email" name="email">
        <label for="message">Your Message</label>
        <textarea id="message" name="message" rows="5"></textarea>
        <select name="department">
            <option>Sales</option>
            <option>Support</option>
            <option>General Inquiry</option>
        </select>
        <button type="submit">Send Message</button>
    </form>
    """
    tree = parse_html(_wrap_article(noise_after=form))
    body = extract_text_content(tree)
    assert body is not None
    assert "Your Name" not in body
    assert "Your Email" not in body
    assert "Send Message" not in body
    assert "General Inquiry" not in body


# ##################################################################
# test strips signup class
# elements with signup class should be stripped
def test_strips_signup_class():
    signup = """
    <div class="signup">
        <h2>Create your free account today for unlimited access to all content</h2>
        <p>Join millions of readers who trust us for their daily news coverage.</p>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=signup))
    body = extract_text_content(tree)
    assert body is not None
    assert "free account" not in body


# ===================================================================
# SIDEBAR AND WIDGET NOISE TESTS
# ===================================================================


# ##################################################################
# test strips sidebar
# aside and sidebar elements should be removed
def test_strips_sidebar():
    sidebar = """
    <aside class="sidebar">
        <h3>Most Popular Articles This Week</h3>
        <ul>
            <li><a href="/1">How to invest in cryptocurrency safely</a></li>
            <li><a href="/2">Ten tips for better sleep quality tonight</a></li>
            <li><a href="/3">The best restaurants in downtown Portland</a></li>
        </ul>
    </aside>
    """
    tree = parse_html(_wrap_article(noise_after=sidebar))
    body = extract_text_content(tree)
    assert body is not None
    assert "cryptocurrency" not in body
    assert "better sleep" not in body
    assert "Portland" not in body


# ##################################################################
# test strips widget class
# elements with class "widget" should be removed
def test_strips_widget_class():
    widget = """
    <div class="widget">
        <h3>Weather Forecast for Your Area</h3>
        <p>Today: Sunny with a high of twenty-five degrees and light winds from the south.</p>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=widget))
    body = extract_text_content(tree)
    assert body is not None
    assert "Weather Forecast" not in body


# ##################################################################
# test strips related articles
# related/recommended articles sections should be stripped
def test_strips_related_articles():
    related = """
    <div class="related">
        <h3>You Might Also Like These Articles</h3>
        <ul>
            <li><a href="/related1">Five ways to save money on your energy bills</a></li>
            <li><a href="/related2">The future of electric vehicles in America</a></li>
            <li><a href="/related3">Expert predictions for the housing market</a></li>
        </ul>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=related))
    body = extract_text_content(tree)
    assert body is not None
    assert "You Might Also Like" not in body
    assert "energy bills" not in body


# ##################################################################
# test strips trending section
# trending/popular content blocks should not leak into article text
def test_strips_trending_section():
    trending = """
    <div class="trending">
        <h3>Trending Now Across the Network</h3>
        <p>Celebrity news: Famous actor spotted at exclusive restaurant opening event.</p>
        <p>Sports update: Local team wins championship in dramatic overtime finish.</p>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=trending))
    body = extract_text_content(tree)
    assert body is not None
    assert "Trending Now" not in body
    assert "Famous actor" not in body


# ##################################################################
# test strips complementary role
# elements with role=complementary (sidebars) should be stripped
def test_strips_complementary_role():
    sidebar = """
    <div role="complementary">
        <p>About the Author: Jane Smith is a senior economics correspondent with twenty years
        of experience covering global financial markets and monetary policy developments.</p>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=sidebar))
    body = extract_text_content(tree)
    assert body is not None
    assert "About the Author" not in body


# ===================================================================
# SOCIAL MEDIA AND SHARING NOISE TESTS
# ===================================================================


# ##################################################################
# test strips social sharing buttons
# share buttons for facebook, twitter etc. should not appear
def test_strips_social_sharing_buttons():
    social = """
    <div class="social">
        <a href="https://facebook.com/share">Share on Facebook</a>
        <a href="https://twitter.com/share">Share on Twitter</a>
        <a href="https://linkedin.com/share">Share on LinkedIn</a>
        <a href="mailto:?subject=article">Email This Article</a>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=social))
    body = extract_text_content(tree)
    assert body is not None
    assert "Share on Facebook" not in body
    assert "Share on Twitter" not in body
    assert "Email This Article" not in body


# ##################################################################
# test strips share class
# elements with class "share" or "sharing" should be stripped
def test_strips_share_class():
    share = """
    <div class="sharing">
        <span>Share this article with your friends and colleagues on social media</span>
        <button>Copy Link</button>
        <button>Print Article</button>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=share))
    body = extract_text_content(tree)
    assert body is not None
    assert "Share this article" not in body


# ===================================================================
# COOKIE AND CONSENT NOISE TESTS
# ===================================================================


# ##################################################################
# test strips cookie banner
# cookie consent banners should be completely removed
def test_strips_cookie_banner():
    cookie = """
    <div class="cookie">
        <p>We use cookies to improve your experience. By continuing to browse this site you
        agree to our use of cookies as described in our privacy policy document.</p>
        <button>Accept All Cookies</button>
        <button>Manage Preferences</button>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=cookie))
    body = extract_text_content(tree)
    assert body is not None
    assert "cookies" not in body.lower()
    assert "Accept All" not in body
    assert "Manage Preferences" not in body


# ##################################################################
# test strips consent class
# gdpr consent overlays should be stripped
def test_strips_consent_class():
    consent = """
    <div class="consent">
        <h2>Privacy Settings and Cookie Preferences</h2>
        <p>Please select which types of cookies you would like to allow on this website.</p>
        <label><input type="checkbox"> Essential cookies that are required for basic functions</label>
        <label><input type="checkbox"> Analytics cookies for tracking visitor statistics</label>
        <button>Save My Preferences</button>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=consent))
    body = extract_text_content(tree)
    assert body is not None
    assert "Privacy Settings" not in body
    assert "Save My Preferences" not in body


# ===================================================================
# FOOTER NOISE TESTS
# ===================================================================


# ##################################################################
# test strips footer
# page footer with copyright, links, and legal text should be stripped
def test_strips_footer():
    footer = """
    <footer>
        <p>Copyright 2024 NewsDaily Inc. All rights reserved worldwide.</p>
        <a href="/privacy">Privacy Policy</a>
        <a href="/terms">Terms of Service</a>
        <a href="/contact">Contact Us</a>
        <p>123 Media Street, New York, NY 10001</p>
    </footer>
    """
    tree = parse_html(_wrap_article(noise_after=footer))
    body = extract_text_content(tree)
    assert body is not None
    assert "Copyright" not in body
    assert "Privacy Policy" not in body
    assert "Terms of Service" not in body
    assert "Media Street" not in body


# ##################################################################
# test strips contentinfo role
# elements with role=contentinfo should be stripped
def test_strips_contentinfo_role():
    footer = """
    <div role="contentinfo">
        <p>Published by MediaCorp International. Unauthorized reproduction is prohibited.</p>
        <a href="/sitemap">Sitemap</a>
        <a href="/rss">RSS Feed</a>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=footer))
    body = extract_text_content(tree)
    assert body is not None
    assert "MediaCorp" not in body


# ===================================================================
# COMMENT SECTION NOISE TESTS
# ===================================================================


# ##################################################################
# test strips comment section
# user comments should not appear in the article text
def test_strips_comment_section():
    comments = """
    <div class="comments">
        <h3>Reader Comments</h3>
        <div class="comment">
            <p><strong>JohnDoe42</strong>: I think this analysis misses the point entirely.
            The real issue is monetary policy, not consumer spending patterns.</p>
        </div>
        <div class="comment">
            <p><strong>EconFan99</strong>: Great article! Very informative and well-researched
            with excellent data visualizations throughout the piece.</p>
        </div>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=comments))
    body = extract_text_content(tree)
    assert body is not None
    assert "JohnDoe42" not in body
    assert "misses the point" not in body
    assert "EconFan99" not in body


# ##################################################################
# test strips disqus comments
# disqus embedded comment threads should be stripped
def test_strips_disqus_comments():
    disqus = """
    <div id="disqus_thread" class="disqus">
        <p>Loading comments from the Disqus platform. Please wait while we fetch the discussion.</p>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=disqus))
    body = extract_text_content(tree)
    assert body is not None
    assert "Disqus" not in body


# ===================================================================
# POPUP AND MODAL NOISE TESTS
# ===================================================================


# ##################################################################
# test strips popup class
# popup overlays should not leak into article text
def test_strips_popup_class():
    popup = """
    <div class="popup">
        <h2>Wait! Before you go, check out our exclusive special offer for new subscribers</h2>
        <p>Get unlimited access to all premium content for just nine dollars per month.</p>
        <button>Claim Your Offer Now</button>
        <button>No Thanks</button>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=popup))
    body = extract_text_content(tree)
    assert body is not None
    assert "Before you go" not in body
    assert "nine dollars" not in body


# ##################################################################
# test strips modal class
# modal dialogs should not appear in extracted text
def test_strips_modal_class():
    modal = """
    <div class="modal">
        <h2>Subscribe to our Premium Plan for full access to all articles</h2>
        <p>You have read three of your five free articles this month.</p>
        <button>Subscribe for Premium Access</button>
        <a href="#">Maybe Later</a>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=modal))
    body = extract_text_content(tree)
    assert body is not None
    assert "Premium Plan" not in body
    assert "free articles" not in body


# ##################################################################
# test strips overlay class
# overlay elements should be stripped
def test_strips_overlay_class():
    overlay = """
    <div class="overlay">
        <p>This content is available exclusively to registered members of our platform.</p>
        <button>Register Free</button>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=overlay))
    body = extract_text_content(tree)
    assert body is not None
    assert "exclusively to registered" not in body


# ===================================================================
# HTML FORMATTING STRIPPING TESTS
# ===================================================================


# ##################################################################
# test strips bold tags
# <b> and <strong> tags should be removed, leaving only plain text
def test_strips_bold_tags():
    html = """
    <html><body>
        <p>The <strong>president</strong> announced a <b>major policy change</b> that will
        affect millions of citizens across the country starting from next month onward.</p>
        <p>Critics argue that the <strong>proposed legislation</strong> fails to address the
        fundamental issues facing the healthcare system in its current implementation.</p>
        <p>Supporters maintain that the reforms represent a significant step forward for the
        nation and will bring much-needed improvements to public services and infrastructure.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "<strong>" not in body
    assert "<b>" not in body
    assert "president" in body
    assert "major policy change" in body


# ##################################################################
# test strips italic tags
# <i> and <em> tags should be removed, leaving only plain text
def test_strips_italic_tags():
    html = """
    <html><body>
        <p>The report, titled <em>Economic Outlook for the Coming Decade</em>, was published
        by the International Monetary Fund earlier this week at their annual conference.</p>
        <p>According to the <i>Financial Times</i>, the decision was not unexpected given the
        recent trends in global commodity prices and currency exchange rate fluctuations.</p>
        <p>Market analysts have been closely watching these developments for signs of broader
        economic shifts that could impact investment strategies in the coming fiscal year.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "<em>" not in body
    assert "<i>" not in body
    assert "Economic Outlook" in body
    assert "Financial Times" in body


# ##################################################################
# test strips span tags
# <span> tags with various styling should produce clean plain text
def test_strips_span_tags():
    html = """
    <html><body>
        <p>The <span class="highlight">stock market</span> rose by
        <span style="color: green; font-weight: bold;">three percent</span> in early trading
        on Monday morning following the release of positive employment data.</p>
        <p>Economists had predicted a more modest increase of around one and a half percent
        based on their analysis of leading economic indicators published last week.</p>
        <p>The unexpected strength in the jobs report suggests that consumer confidence remains
        resilient despite ongoing concerns about inflation and rising interest rates globally.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "<span" not in body
    assert "stock market" in body
    assert "three percent" in body


# ##################################################################
# test strips nested formatting
# deeply nested formatting tags should all be stripped to plain text
def test_strips_nested_formatting():
    html = """
    <html><body>
        <p>The <strong><em>critically important</em></strong> report contained
        <b><i><u>several key findings</u></i></b> that researchers described as groundbreaking
        in their implications for the field of climate science and environmental policy.</p>
        <p>Among the most significant conclusions was evidence that ocean temperatures have risen
        at a rate substantially faster than previous models had predicted over the past decade.</p>
        <p>The research team emphasized that immediate action is needed to prevent the most severe
        projected consequences outlined in their comprehensive multi-year global assessment.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "<strong>" not in body
    assert "<em>" not in body
    assert "<b>" not in body
    assert "<i>" not in body
    assert "<u>" not in body
    assert "critically important" in body
    assert "several key findings" in body


# ##################################################################
# test strips br tags into whitespace
# <br> tags should become whitespace, not be visible as tags
def test_strips_br_tags():
    html = """
    <html><body>
        <p>First line of the paragraph that continues with important content.<br>
        Second line after a break that also has meaningful article content.<br>
        Third line completing the thought with additional relevant information.</p>
        <p>Another paragraph that contains enough text to pass the minimum content length
        filter and contribute to the overall body of the extracted article text.</p>
        <p>A final paragraph ensuring the total extracted content exceeds the minimum required
        length threshold of one hundred characters for successful extraction results.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "<br>" not in body
    assert "<br/>" not in body
    assert "First line" in body
    assert "Second line" in body


# ##################################################################
# test strips sup and sub tags
# superscript and subscript tags should be stripped to plain text
def test_strips_sup_and_sub_tags():
    html = """
    <html><body>
        <p>The study found that carbon dioxide levels have increased to 420 parts per million,
        with CO<sub>2</sub> emissions rising by 1.5<sup>percent</sup> compared to the
        previous measurement period taken during the spring of last year.</p>
        <p>Researchers noted that the rate of increase was consistent with projections made by
        the climate modeling team at the university environmental sciences department.</p>
        <p>Further analysis revealed correlations between industrial output in developing nations
        and the observed atmospheric changes recorded at monitoring stations worldwide.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "<sub>" not in body
    assert "<sup>" not in body
    assert "CO" in body
    assert "420 parts per million" in body


# ##################################################################
# test strips mark tags
# <mark> highlight tags should be stripped to plain text
def test_strips_mark_tags():
    html = """
    <html><body>
        <p>The investigation revealed that <mark>financial irregularities</mark> had been
        occurring for at least <mark>three consecutive years</mark> before the audit team
        discovered the discrepancies during their routine quarterly review process.</p>
        <p>Company executives denied any knowledge of the irregularities and pledged full
        cooperation with the ongoing regulatory investigation being conducted by authorities.</p>
        <p>Shareholders reacted negatively to the news, with the company stock price dropping
        significantly in after-hours trading following the public disclosure of findings.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "<mark>" not in body
    assert "financial irregularities" in body
    assert "three consecutive years" in body


# ##################################################################
# test whitespace normalisation
# multiple spaces, tabs, and newlines within text should collapse to single spaces
def test_whitespace_normalisation():
    html = """
    <html><body>
        <p>This    paragraph     has     multiple    spaces     scattered     throughout
        the    entire     text     that     should     all     be     collapsed.</p>
        <p>This\tparagraph\thas\ttabs\tinstead\tof\tspaces\tand\tthey\tshould\talso
        be\tnormalized\tinto\tsingle\tspaces\tfor\treadability.</p>
        <p>And this paragraph has
        newlines
        embedded
        within it that should be collapsed into single spaces during extraction processing.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "  " not in body
    assert "\t" not in body


# ===================================================================
# LINK PRESERVATION TESTS
# ===================================================================


# ##################################################################
# test preserves link text in paragraphs
# anchor text within paragraphs is part of the article and must be kept
def test_preserves_link_text_in_paragraphs():
    html = """
    <html><body>
        <p>According to a <a href="https://example.com/report">recent report by the Federal
        Reserve</a>, inflation has moderated to an annual rate of two point four percent,
        down from the peak of nine point one percent recorded in June of last year.</p>
        <p>The <a href="https://example.com/imf">International Monetary Fund</a> has also
        revised its growth forecast upward, projecting global GDP expansion of three point
        two percent for the current fiscal year in their latest assessment.</p>
        <p>These developments have been welcomed by market participants who see them as
        confirmation that the economic soft landing scenario is now the most likely outcome.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "recent report by the Federal Reserve" in body
    assert "International Monetary Fund" in body
    assert "<a " not in body
    assert "href" not in body


# ##################################################################
# test preserves multiple links in same paragraph
# several links within one paragraph should all have their text preserved
def test_preserves_multiple_links_in_same_paragraph():
    html = """
    <html><body>
        <p>The summit was attended by leaders from <a href="/us">the United States</a>,
        <a href="/uk">the United Kingdom</a>, <a href="/fr">France</a>, and
        <a href="/de">Germany</a>, who discussed trade policy and climate change commitments
        for the remainder of the decade during their two-day session.</p>
        <p>A joint statement released after the meeting outlined several key agreements on
        carbon emissions targets and renewable energy investment goals going forward.</p>
        <p>Environmental groups praised the commitments but cautioned that implementation
        details remain vague and will require sustained political will to achieve results.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "the United States" in body
    assert "the United Kingdom" in body
    assert "France" in body
    assert "Germany" in body


# ##################################################################
# test preserves inline link text without href
# link text is content even when appearing inline with other formatting
def test_preserves_inline_link_text_without_markup():
    html = """
    <html><body>
        <p>As <a href="/profile"><strong>Professor Smith</strong></a> explained in her
        <a href="/paper"><em>landmark paper</em></a>, the evidence strongly suggests that
        early intervention programs yield significantly better outcomes for participants.</p>
        <p>The findings have been corroborated by subsequent studies conducted at several
        major research universities across North America and Western Europe since publication.</p>
        <p>Policy makers are now considering how best to incorporate these research findings
        into existing educational frameworks and social services delivery programs nationwide.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "Professor Smith" in body
    assert "landmark paper" in body
    assert "<a " not in body
    assert "<strong>" not in body
    assert "<em>" not in body


# ===================================================================
# IFRAME AND EMBEDDED CONTENT TESTS
# ===================================================================


# ##################################################################
# test strips iframes
# embedded iframes (ads, videos, widgets) should be completely removed
def test_strips_iframes():
    html = f"""
    <html><body>
        <iframe src="https://ads.example.com/banner" width="728" height="90"></iframe>
        {ARTICLE_BODY}
        <iframe src="https://youtube.com/embed/abc123" width="560" height="315"></iframe>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "ads.example.com" not in body
    assert "youtube.com" not in body
    assert "global economy" in body


# ##################################################################
# test strips noscript fallbacks
# noscript tags often contain tracking pixels or fallback ad content
def test_strips_noscript_fallbacks():
    html = f"""
    <html><body>
        <noscript>
            <img src="https://tracking.example.com/pixel.gif" alt="tracking">
            <p>Please enable JavaScript to view the interactive charts and data visualizations.</p>
        </noscript>
        {ARTICLE_BODY}
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "enable JavaScript" not in body
    assert "tracking" not in body


# ===================================================================
# SCRIPT AND STYLE NOISE TESTS
# ===================================================================


# ##################################################################
# test strips inline script content
# javascript inside script tags must never leak into text
def test_strips_inline_script_content():
    html = f"""
    <html><body>
        <script>
            var adConfig = {{ slot: "top-banner", sizes: [[728, 90]] }};
            googletag.cmd.push(function() {{ googletag.display("top-banner"); }});
        </script>
        <script type="application/ld+json">
            {{"@type": "NewsArticle", "headline": "Economy Report"}}
        </script>
        {ARTICLE_BODY}
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "adConfig" not in body
    assert "googletag" not in body
    assert "NewsArticle" not in body


# ##################################################################
# test strips style blocks
# css inside style tags must never appear in extracted text
def test_strips_style_blocks():
    html = f"""
    <html><head>
        <style>
            .article {{ font-size: 16px; line-height: 1.6; }}
            .ad-banner {{ display: block; width: 728px; height: 90px; }}
            @media (max-width: 768px) {{ .sidebar {{ display: none; }} }}
        </style>
    </head><body>{ARTICLE_BODY}</body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "font-size" not in body
    assert "ad-banner" not in body
    assert "@media" not in body


# ===================================================================
# CALL-TO-ACTION NOISE TESTS
# ===================================================================


# ##################################################################
# test strips cta class
# call-to-action buttons and boxes should not appear
def test_strips_cta_class():
    cta = """
    <div class="cta">
        <h2>Ready to take your investing to the next level with expert guidance?</h2>
        <p>Join our premium membership today and get access to exclusive analysis reports.</p>
        <button>Start Your Free Trial Now</button>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=cta))
    body = extract_text_content(tree)
    assert body is not None
    assert "take your investing" not in body
    assert "Free Trial" not in body


# ##################################################################
# test strips call to action class
# hyphenated call-to-action class should also be caught
def test_strips_call_to_action_class():
    cta = """
    <div class="call-to-action">
        <p>Do not miss out on the latest market insights delivered to your email daily.</p>
        <button>Sign Up for Free</button>
    </div>
    """
    tree = parse_html(_wrap_article(noise_after=cta))
    body = extract_text_content(tree)
    assert body is not None
    assert "miss out" not in body


# ===================================================================
# COMPLEX REALISTIC PAGE TESTS
# ===================================================================


# ##################################################################
# test realistic news article page
# a full news page with header, nav, ads, sidebar, footer, and article
def test_realistic_news_article_page():
    html = """
    <html>
    <head><title>Economy Shows Recovery Signs | NewsDaily</title></head>
    <body>
        <header>
            <div class="logo">NewsDaily</div>
            <nav>
                <a href="/">Home</a>
                <a href="/politics">Politics</a>
                <a href="/business">Business</a>
                <a href="/tech">Technology</a>
                <a href="/sports">Sports</a>
            </nav>
            <form action="/search"><input type="text" placeholder="Search"><button>Go</button></form>
        </header>

        <div class="ad">
            <p>Special promotional offer from our valued advertising partner this season.</p>
        </div>

        <div class="breadcrumb">
            <a href="/">Home</a> &gt; <a href="/business">Business</a> &gt; Markets
        </div>

        <main>
            <article>
                <h1>Global Economy Shows Strong Recovery Signs in Third Quarter Report</h1>
                <p>The global economy showed impressive recovery signs in the third quarter
                of this year, with growth exceeding analyst expectations across major regions.
                Consumer spending returned to healthy levels in most developed economies.</p>
                <p>According to the <a href="/imf-report">International Monetary Fund</a>,
                global GDP grew by three point two percent, marking the strongest quarterly
                performance since the end of the pandemic-related economic disruptions.</p>
                <p>Technology and healthcare sectors led the gains, with companies in both
                industries reporting earnings that surpassed Wall Street consensus estimates
                by significant margins during the latest quarterly reporting season.</p>
                <p>Labor markets also showed improvement, with unemployment falling to four
                point one percent in the United States and similar declines being recorded
                across the European Union member states during the same period.</p>
            </article>
        </main>

        <div class="ad">
            <p>Best cloud hosting deals available this month from TechHost premium services.</p>
        </div>

        <aside class="sidebar">
            <h3>Most Read This Week</h3>
            <ul>
                <li><a href="/1">How artificial intelligence is transforming healthcare</a></li>
                <li><a href="/2">Ten best investment strategies for beginners this year</a></li>
            </ul>
        </aside>

        <div class="social">
            <a href="#">Share on Facebook</a>
            <a href="#">Share on Twitter</a>
        </div>

        <div class="comments">
            <h3>Reader Comments</h3>
            <p>UserABC: Great analysis of the current market conditions and trends.</p>
        </div>

        <div class="newsletter">
            <h3>Get Our Daily Newsletter</h3>
            <form><input type="email" placeholder="email"><button>Subscribe</button></form>
        </div>

        <footer>
            <p>Copyright 2024 NewsDaily. All rights reserved.</p>
            <a href="/privacy">Privacy</a>
            <a href="/terms">Terms</a>
        </footer>
    </body>
    </html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None

    assert "global economy showed impressive recovery" in body.lower()
    assert "International Monetary Fund" in body
    assert "Technology and healthcare" in body
    assert "Labor markets" in body

    assert "NewsDaily" not in body
    assert "Home" not in body.split("global")[0]
    assert "Politics" not in body.split("global")[0]
    assert "promotional offer" not in body
    assert "TechHost" not in body
    assert "Most Read" not in body
    assert "artificial intelligence" not in body
    assert "Share on Facebook" not in body
    assert "UserABC" not in body
    assert "Daily Newsletter" not in body
    assert "Copyright" not in body
    assert "Privacy" not in body


# ##################################################################
# test realistic blog post page
# a blog page with author info, tags, related posts, and ads
def test_realistic_blog_post_page():
    html = """
    <html>
    <head><title>Understanding Machine Learning - TechBlog</title></head>
    <body>
        <header>
            <div class="logo">TechBlog</div>
            <nav>
                <a href="/">Home</a>
                <a href="/tutorials">Tutorials</a>
                <a href="/reviews">Reviews</a>
            </nav>
        </header>

        <div class="cookie">
            <p>This website uses cookies for analytics and personalized advertising content.</p>
            <button>Accept All</button>
        </div>

        <div class="banner">
            <p>New course available: Master Python programming in thirty days flat.</p>
        </div>

        <article>
            <h1>Understanding Machine Learning: A Comprehensive Beginner Guide</h1>
            <p>Machine learning is a subset of artificial intelligence that enables computers
            to learn from data without being explicitly programmed for every possible scenario.
            This technology has revolutionized many industries in recent years.</p>
            <p>At its core, machine learning algorithms identify patterns in large datasets
            and use those patterns to make predictions or decisions about new unseen data.
            The process involves training a model on historical examples.</p>
            <p>There are three main types of machine learning: supervised learning where the
            algorithm learns from labeled examples, unsupervised learning where it finds hidden
            patterns, and reinforcement learning where it learns through trial and error.</p>
            <p>Popular frameworks for implementing machine learning include
            <a href="https://tensorflow.org">TensorFlow</a>,
            <a href="https://pytorch.org">PyTorch</a>, and
            <a href="https://scikit-learn.org">scikit-learn</a>, each with
            different strengths depending on the specific use case requirements.</p>
        </article>

        <div class="ad">
            <p>Sponsored: Best laptops for machine learning development work in 2024.</p>
        </div>

        <div class="related">
            <h3>Related Articles You May Enjoy</h3>
            <a href="/deep-learning">Introduction to Deep Learning Networks</a>
            <a href="/nlp">Natural Language Processing Basics Tutorial</a>
        </div>

        <div class="signup">
            <h3>Join our developer community for exclusive tutorials and resources</h3>
            <form><input type="email"><button>Join Now</button></form>
        </div>

        <footer>
            <p>TechBlog 2024. Built with passion for technology.</p>
        </footer>
    </body>
    </html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None

    assert "Machine learning is a subset" in body
    assert "three main types" in body
    assert "TensorFlow" in body
    assert "PyTorch" in body
    assert "scikit-learn" in body

    assert "TechBlog" not in body
    assert "Tutorials" not in body.split("Machine")[0]
    assert "cookies" not in body.lower()
    assert "Master Python" not in body
    assert "Best laptops" not in body
    assert "Related Articles" not in body
    assert "Deep Learning" not in body
    assert "developer community" not in body
    assert "Built with passion" not in body


# ##################################################################
# test page with aggressive inline advertising
# ads scattered throughout article paragraphs should all be stripped
def test_page_with_aggressive_inline_advertising():
    html = """
    <html><body>
        <div class="ad"><p>Top banner advertisement for summer sale event happening now.</p></div>

        <p>Scientists at the European Organization for Nuclear Research have announced a major
        breakthrough in particle physics that could reshape our understanding of the universe
        and the fundamental forces that govern the behavior of matter at quantum scales.</p>

        <div class="sponsored"><p>Brought to you by QuantumTech: Leaders in quantum computing
        solutions for enterprise and research institutions worldwide.</p></div>

        <p>The discovery involves a previously unobserved interaction between quarks and gluons
        at extremely high energy levels that were only achievable with the latest upgrades to
        the Large Hadron Collider facility located beneath the border of France and Switzerland.</p>

        <div class="advertisement"><p>Limited offer: Subscribe to Science Weekly magazine and
        save forty percent on your annual subscription this holiday season.</p></div>

        <p>Lead researcher Dr. Maria Vasquez described the findings as extraordinary, noting
        that the team had spent over three years collecting and analyzing the experimental data
        before they felt confident enough to publish their results in a peer-reviewed journal.</p>

        <div class="promo"><p>Download our free science app for daily discoveries and news
        updates from leading research institutions around the world.</p></div>

        <p>The implications of this discovery extend beyond theoretical physics. Potential
        applications include advances in quantum computing, materials science, and medical
        imaging technology that could benefit patients and researchers in equal measure.</p>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None

    assert "European Organization for Nuclear Research" in body
    assert "quarks and gluons" in body
    assert "Dr. Maria Vasquez" in body
    assert "quantum computing, materials science" in body

    assert "summer sale" not in body
    assert "QuantumTech" not in body
    assert "Science Weekly" not in body
    assert "free science app" not in body


# ##################################################################
# test search role stripped
# elements with role=search should be stripped
def test_search_role_stripped():
    search = """
    <div role="search">
        <label>Search our entire archive of articles and multimedia content</label>
        <input type="text" placeholder="Type your search terms here">
        <button>Search Now</button>
    </div>
    """
    tree = parse_html(_wrap_article(noise_before=search))
    body = extract_text_content(tree)
    assert body is not None
    assert "Search our entire archive" not in body


# ##################################################################
# test button tags stripped
# standalone button elements should not contribute text
def test_button_tags_stripped():
    html = f"""
    <html><body>
        <button>Click here to load more articles</button>
        <button class="close">Close this notification permanently</button>
        {ARTICLE_BODY}
        <button>Show all reader comments below</button>
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "Click here to load" not in body
    assert "Close this notification" not in body
    assert "Show all reader comments" not in body


# ##################################################################
# test details and summary stripped
# expandable details elements should not leak text
def test_details_and_summary_stripped():
    html = f"""
    <html><body>
        <details>
            <summary>Click to expand the methodology section of this report</summary>
            <p>Data was collected from a random sample of ten thousand participants using
            online surveys distributed through partner organizations in twelve countries.</p>
        </details>
        {ARTICLE_BODY}
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "Click to expand" not in body
    assert "random sample" not in body


# ##################################################################
# test dialog element stripped
# html5 dialog modals should be stripped
def test_dialog_element_stripped():
    html = f"""
    <html><body>
        <dialog open>
            <p>Your session has expired. Please log in again to continue reading this article.</p>
            <button>Log In Again</button>
        </dialog>
        {ARTICLE_BODY}
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "session has expired" not in body


# ##################################################################
# test menu element stripped
# html5 menu elements should be stripped
def test_menu_element_stripped():
    html = f"""
    <html><body>
        <menu>
            <li><button>Cut</button></li>
            <li><button>Copy</button></li>
            <li><button>Paste</button></li>
        </menu>
        {ARTICLE_BODY}
    </body></html>
    """
    tree = parse_html(html)
    body = extract_text_content(tree)
    assert body is not None
    assert "Cut" not in body
    assert "Copy" not in body
    assert "Paste" not in body
