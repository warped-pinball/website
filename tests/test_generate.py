import json
import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

import scripts.generate as generate  # noqa: E402


def test_calculate_json_hash_deterministic():
    data1 = {"a": 1, "b": 2}
    data2 = {"b": 2, "a": 1}
    hash1 = generate.calculate_json_hash(data1)
    hash2 = generate.calculate_json_hash(data2)
    assert hash1 == hash2


def test_fetch_update_json_success(monkeypatch):
    json_line = json.dumps({"version": "1.0"})

    class MockResponse:
        status_code = 200
        text = json_line + "\nBINARYDATA"

    def mock_get(url):
        return MockResponse()

    monkeypatch.setattr(generate.requests, "get", mock_get)
    result = generate.fetch_update_json("http://example.com/update.json")
    assert result == {"version": "1.0"}


def test_fetch_update_json_failure(monkeypatch):
    class MockResponse:
        status_code = 404
        text = ""

    def mock_get(url):
        return MockResponse()

    monkeypatch.setattr(generate.requests, "get", mock_get)
    result = generate.fetch_update_json("http://example.com/missing.json")
    assert result is None


def test_parse_release_versions():
    body = (
        "Some notes\n"
        "## Versions\n"
        "**Vector**: `1.3.11-dev83`\n"
        "**Sys11**: `1.0.0-dev83`\n"
        "**WPC**: `0.0.0-dev83`\n"
        "**EM**: `0.0.1-dev83`\n"
        "<!-- END VERSIONS SECTION -->\nMore text"
    )
    versions = generate.parse_release_versions(body)
    assert versions == {
        "vector": "1.3.11-dev83",
        "sys11": "1.0.0-dev83",
        "wpc": "0.0.0-dev83",
        "em": "0.0.1-dev83",
    }


def test_parse_release_versions_missing():
    body = "No version info"
    versions = generate.parse_release_versions(body)
    assert versions == {}


def test_release_notes_to_html_sanitizes_and_strips_images():
    md = "Hello! ![img](http://example.com/a.png) <script>alert('x')</script>"
    html = generate.release_notes_to_html(md)
    assert "<img" not in html
    assert "script" not in html
    assert "Hello" in html
