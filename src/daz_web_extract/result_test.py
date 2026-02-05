import json

from daz_web_extract.result import ExtractionResult, make_success, make_failure


# ##################################################################
# test make success populates all fields
# verify every field is correctly set on a successful result
def test_make_success_populates_all_fields():
    result = make_success(
        url="https://example.com",
        title="Example Domain",
        body="This domain is for use in examples.",
        fetch_method="httpx",
        status_code=200,
        elapsed_ms=150,
    )
    assert result.success is True
    assert result.url == "https://example.com"
    assert result.title == "Example Domain"
    assert result.body == "This domain is for use in examples."
    assert result.error is None
    assert result.fetch_method == "httpx"
    assert result.status_code == 200
    assert result.content_length == len("This domain is for use in examples.")
    assert result.elapsed_ms == 150


# ##################################################################
# test make failure populates all fields
# verify every field is correctly set on a failed result
def test_make_failure_populates_all_fields():
    result = make_failure(
        url="https://bad.example.com",
        error="Connection refused",
        fetch_method="httpx",
        status_code=None,
        elapsed_ms=50,
    )
    assert result.success is False
    assert result.url == "https://bad.example.com"
    assert result.title is None
    assert result.body is None
    assert result.error == "Connection refused"
    assert result.fetch_method == "httpx"
    assert result.status_code is None
    assert result.content_length == 0
    assert result.elapsed_ms == 50


# ##################################################################
# test to dict roundtrip
# verify dict serialization produces valid structure
def test_to_dict_roundtrip():
    result = make_success(
        url="https://example.com",
        title="Test",
        body="Body text here",
        fetch_method="trafilatura",
        status_code=200,
        elapsed_ms=100,
    )
    d = result.to_dict()
    assert isinstance(d, dict)
    assert d["success"] is True
    assert d["url"] == "https://example.com"
    assert d["title"] == "Test"
    assert d["body"] == "Body text here"
    assert d["content_length"] == len("Body text here")
    reconstructed = ExtractionResult(**d)
    assert reconstructed == result


# ##################################################################
# test to json roundtrip
# verify json serialization and deserialization preserve all fields
def test_to_json_roundtrip():
    result = make_failure(
        url="https://example.com",
        error="Timeout",
        fetch_method="playwright",
        status_code=None,
        elapsed_ms=30000,
    )
    j = result.to_json()
    parsed = json.loads(j)
    assert parsed["success"] is False
    assert parsed["error"] == "Timeout"
    assert parsed["fetch_method"] == "playwright"
    reconstructed = ExtractionResult(**parsed)
    assert reconstructed == result


# ##################################################################
# test content length computed from body
# make sure content_length reflects actual body length
def test_content_length_computed_from_body():
    body = "a" * 500
    result = make_success(
        url="https://example.com",
        title=None,
        body=body,
        fetch_method="httpx",
        status_code=200,
        elapsed_ms=10,
    )
    assert result.content_length == 500


# ##################################################################
# test frozen dataclass
# ensure the result is immutable
def test_frozen_dataclass():
    result = make_success(
        url="https://example.com",
        title="Test",
        body="Body",
        fetch_method="httpx",
        status_code=200,
        elapsed_ms=10,
    )
    try:
        result.success = False
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass
