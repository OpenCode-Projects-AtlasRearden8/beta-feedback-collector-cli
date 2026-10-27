"""Optional theme brainstorm via an OpenAI-compatible chat endpoint.

Defaults to a local Ollama server (http://127.0.0.1:11434/v1). This module
deliberately never touches API keys: it is built for keyless local servers.
If your gateway requires a header, set it yourself outside this tool.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_MODEL = "llama3.1"


class BrainstormError(RuntimeError):
    pass


def brainstorm_themes(items, base_url=DEFAULT_BASE_URL, model=DEFAULT_MODEL, timeout=30) -> str:
    """Ask the local model for plot/theme brainstorm notes based on the feedback."""
    flags = [item for item in items if item.kind == "plot"]
    digest = "\n".join(f"- Ch {item.chapter} ({item.reader}): {item.text}" for item in flags[:25])
    if not digest:
        digest = "\n".join(f"- Ch {item.chapter} ({item.reader}): {item.text}" for item in items[:10])
    prompt = (
        "You are a friendly book-doctor assistant. Below are plot-level beta-reader "
        "comments for a manuscript. Brainstorm 5 concrete theme/story ideas that keep "
        "what readers loved and fix what confused them. Plain English, one line each.\n\n"
        f"Beta feedback:\n{digest}"
    )
    payload = json.dumps(
        {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    url = f"{base_url.rstrip('/')}/chat/completions"
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise BrainstormError(
            f"Could not reach brainstorm endpoint at {url} "
            f"(is your local server running?): {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise BrainstormError(f"Unexpected non-JSON response from {url}") from exc
    try:
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise BrainstormError(f"Malformed response from {url}") from exc
