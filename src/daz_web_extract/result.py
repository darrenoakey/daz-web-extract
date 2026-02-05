from __future__ import annotations

import json
from dataclasses import dataclass, asdict


# ##################################################################
# extraction result
# structured result from any extraction attempt; never raises, always
# returns success or failure with context for diagnostics
@dataclass(frozen=True)
class ExtractionResult:
    success: bool
    url: str
    title: str | None
    body: str | None
    error: str | None
    fetch_method: str | None
    status_code: int | None
    content_length: int
    elapsed_ms: int

    # ##################################################################
    # to dict
    # convert to plain dict for serialization
    def to_dict(self) -> dict:
        return asdict(self)

    # ##################################################################
    # to json
    # convert to json string
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ##################################################################
# make success
# convenience constructor for successful extractions
def make_success(
    url: str,
    title: str | None,
    body: str,
    fetch_method: str,
    status_code: int | None,
    elapsed_ms: int,
) -> ExtractionResult:
    return ExtractionResult(
        success=True,
        url=url,
        title=title,
        body=body,
        error=None,
        fetch_method=fetch_method,
        status_code=status_code,
        content_length=len(body),
        elapsed_ms=elapsed_ms,
    )


# ##################################################################
# make failure
# convenience constructor for failed extractions
def make_failure(
    url: str,
    error: str,
    fetch_method: str | None,
    status_code: int | None,
    elapsed_ms: int,
) -> ExtractionResult:
    return ExtractionResult(
        success=False,
        url=url,
        title=None,
        body=None,
        error=error,
        fetch_method=fetch_method,
        status_code=status_code,
        content_length=0,
        elapsed_ms=elapsed_ms,
    )
