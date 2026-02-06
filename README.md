![](banner.jpg)

# daz-web-extract

Async Python library that extracts clean title and body text from any URL. It automatically escalates through multiple fetch strategies to handle everything from simple static pages to JavaScript-rendered content. It never throws exceptions — every call returns a structured result indicating success or failure.

## Installation

Requires Python 3.12+.

```bash
pip install daz-web-extract
```

After installing, set up the browser engine for pages that require JavaScript rendering:

```bash
playwright install chromium
```

## Usage

### Python API

The library exposes a single async function `extract` and a result type `ExtractionResult`.

```python
import asyncio
from daz_web_extract import extract, ExtractionResult

result: ExtractionResult = asyncio.run(extract("https://example.com"))

if result.success:
    print(result.title)           # Page title
    print(result.body)            # Clean body text
    print(result.fetch_method)    # Which strategy succeeded
    print(result.content_length)  # Length of body in characters
    print(result.elapsed_ms)      # Total time in milliseconds
    print(result.status_code)     # HTTP status code (if available)
else:
    print(result.error)           # Human-readable error message
```

#### Fetch Strategy

Four tiers escalate automatically until one succeeds:

| Tier | Method | Description |
|------|--------|-------------|
| 1 | `httpx` | Fast async HTTP fetch with lxml extraction (10s timeout) |
| 2 | `trafilatura` | Thread-based extraction via trafilatura (15s timeout) |
| 3 | `playwright-nojs` | Headless browser with JS disabled — fast SSR extraction |
| 4 | `playwright` | Headless browser with JS enabled — full rendering for SPAs (30s timeout) |

Tier 3 detects "requires javascript" phrases in the extracted content and automatically escalates to tier 4 when JavaScript is needed. HTTP 4xx/5xx responses (except 403/429) skip tier 2 and go straight to tier 3.

#### Limiting fetch strategies

Use the `max_tier` parameter to control how far the library escalates:

```python
# Only use fast HTTP fetch (no browser, no trafilatura)
result = await extract("https://example.com", max_tier=1)

# Use HTTP fetch + trafilatura, but skip the browser
result = await extract("https://example.com", max_tier=2)

# Use HTTP fetch + trafilatura + browser without JS
result = await extract("https://example.com", max_tier=3)

# Use all strategies including full JS browser (default)
result = await extract("https://example.com", max_tier=4)
```

#### Serialization

Results can be converted to dictionaries or JSON:

```python
result.to_dict()  # Returns a plain dict
result.to_json()  # Returns a JSON string
```

#### Using in async code

```python
import asyncio
from daz_web_extract import extract

async def main():
    urls = [
        "https://example.com",
        "https://www.iana.org/help/example-domains",
    ]
    results = await asyncio.gather(*[extract(url) for url in urls])
    for r in results:
        print(f"{r.url}: {r.title} ({r.content_length} chars)")

asyncio.run(main())
```

### Command Line

Extract content from a URL via the `run` script:

```bash
./run extract https://example.com
```

Output:

```
Title: Example Domain
Method: httpx
Length: 217 chars
Time: 142ms

Example Domain
This domain is for use in illustrative examples in documents. You may use this
domain in literature without prior coordination or asking for permission.
More information...
```

Get raw JSON output:

```bash
./run extract https://example.com --raw
```

Other commands:

```bash
# Run tests
./run test src/daz_web_extract/result_test.py

# Run linter
./run lint

# Run full quality checks
./run check
```

## Development

Set up a development environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

Run the tests:

```bash
pytest -q src/
```
