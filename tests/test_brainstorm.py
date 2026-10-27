"""Tests for the optional local-LLM brainstorm (offline, mocked).

The brainstorm feature targets OpenAI-compatible endpoints such as a local
Ollama server (http://127.0.0.1:11434/v1) and never sends API keys.
"""

import json
import urllib.error

import pytest

from betafeedback.brainstorm import BrainstormError, brainstorm_themes
from betafeedback.normalize import collect_items

from pathlib import Path


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def read(self) -> bytes:
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _fixtures():
    return collect_items(Path(__file__).parent / "fixtures")


def test_brainstorm_success(monkeypatch):
    calls = []

    def responder(request, timeout=None):
        calls.append({"url": request.full_url, "data": request.data})
        body = {"choices": [{"message": {"content": "1. Keep the motel map scene as book-one's thematic anchor."}}]}
        return FakeResponse(json.dumps(body).encode("utf-8"))

    monkeypatch.setattr("betafeedback.brainstorm.urllib.request.urlopen", responder)
    result = brainstorm_themes(_fixtures(), base_url="http://localhost:11434/v1", model="test-model")
    assert "motel map scene" in result
    request_body = json.loads(calls[0]["data"].decode("utf-8"))
    assert request_body["model"] == "test-model"
    assert "/chat/completions" in calls[0]["url"]


def test_default_is_keyless_local_endpoint():
    import betafeedback.brainstorm as bs

    assert bs.DEFAULT_BASE_URL.startswith("http://127.0.0.1") or bs.DEFAULT_BASE_URL.startswith("http://localhost")
    assert "key" not in bs.DEFAULT_BASE_URL.lower()


def test_brainstorm_connection_error_is_friendly(monkeypatch):
    def responder(request, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("betafeedback.brainstorm.urllib.request.urlopen", responder)
    with pytest.raises(BrainstormError) as excinfo:
        brainstorm_themes(_fixtures(), base_url="http://127.0.0.1:11434/v1")
    assert "is your local server running" in str(excinfo.value)


def test_brainstorm_rejects_malformed_payload(monkeypatch):
    def responder(request, timeout=None):
        return FakeResponse(b'{"object":"list"}')

    monkeypatch.setattr("betafeedback.brainstorm.urllib.request.urlopen", responder)
    with pytest.raises(BrainstormError):
        brainstorm_themes(_fixtures())
