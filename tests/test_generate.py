import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import scripts.generate as generate


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
