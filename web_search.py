"""
Open WebUI tool that queries a local SearxNG instance for web search results.

The `web_search` function validates inputs, applies TTL caching, and issues a
GET request to the configured SearxNG endpoint. Results are normalized into a
JSON-serializable structure with clear error reporting. All configuration is
read from environment variables with sensible defaults. Input validation is
strict and exceptions are raised for unsupported values. HTTP requests use
explicit timeouts and an allowlist guard to prevent unintended destinations.

Examples:
    Correct: ``web_search("minecraft server status", max_results=3)``
    Incorrect: ``web_search(" ", max_results=50)``
"""
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests


TOOL_DESCRIPTION = "Search SearxNG for the top results of a query."
TOOL_EXAMPLES = {
    "correct": [
        "web_search('python asyncio tutorial')",
        "web_search('latest minecraft news', max_results=3)",
    ],
    "incorrect": [
        "web_search('', max_results=5)",
        "web_search('kittens', max_results=25)",
    ],
}


ALLOWED_BASE_URLS = {
    os.environ.get("SEARXNG_BASE_URL", "http://searxng:8080").rstrip("/")
}
DEFAULT_BASE_URL = next(iter(ALLOWED_BASE_URLS))
DEFAULT_TIMEOUT = float(os.environ.get("SEARXNG_TIMEOUT_SECONDS", "10"))
DEFAULT_CACHE_TTL = int(os.environ.get("SEARXNG_CACHE_TTL_SECONDS", "21600"))
MAX_RESULTS_LIMIT = 10
MIN_RESULTS_LIMIT = 1


class TTLCache:
    """A minimal in-memory TTL cache.

    Stores key/value pairs alongside an expiration timestamp. Expired entries
    are purged during access. Designed for deterministic, thread-unsafe usage
    within a single process.
    """

    def __init__(self, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._ttl = ttl_seconds
        self._store: Dict[Any, Any] = {}

    def get(self, key: Any) -> Optional[Any]:
        record = self._store.get(key)
        if not record:
            return None
        expires_at, value = record
        if time.time() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: Any, value: Any) -> None:
        self._store[key] = (time.time() + self._ttl, value)


_cache = TTLCache(DEFAULT_CACHE_TTL)


def _http_get_json(url: str, params: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    """Perform an HTTP GET request and parse JSON response.

    Args:
        url: Full request URL. Must belong to the ALLOWED_BASE_URLS allowlist.
        params: Query parameters to include in the request.
        timeout: Timeout in seconds applied to both connect and read phases.

    Returns:
        A dictionary containing the HTTP status code and parsed JSON data.

    Raises:
        PermissionError: If the URL is not in the allowlist.
        TimeoutError: If the request times out.
        RuntimeError: For non-timeout request errors.
        ValueError: If the response body is not valid JSON when status is 200.
    """

    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base not in ALLOWED_BASE_URLS:
        raise PermissionError("URL not allowed by policy")

    try:
        response = requests.get(url, params=params, timeout=(timeout, timeout))
    except requests.exceptions.Timeout as exc:
        raise TimeoutError("Request timed out") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    status_code = response.status_code
    if status_code != 200:
        return {"status": status_code, "data": None}

    try:
        return {"status": status_code, "data": response.json()}
    except ValueError as exc:
        raise ValueError("Invalid JSON received") from exc


def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Search the configured SearxNG instance and return normalized results.

    Args:
        query: Search query string. Must be non-empty.
        max_results: Maximum number of results to return (clamped between 1 and
            10). Defaults to 5.

    Returns:
        A JSON-serializable dictionary with keys:
            ok (bool): True when results are successfully retrieved.
            query (str): Echo of the search query.
            results (list): Normalized result entries.
            error (dict|None): Structured error details when ok is False.

    Raises:
        ValueError: If query is empty or max_results is out of bounds.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if not isinstance(max_results, int):
        raise ValueError("max_results must be an integer")

    clamped_results = max(MIN_RESULTS_LIMIT, min(MAX_RESULTS_LIMIT, max_results))

    cache_key = (query.strip(), clamped_results)
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        "q": query.strip(),
        "format": "json",
        "language": "en",
        "safesearch": 1,
    }

    try:
        response = _http_get_json(f"{DEFAULT_BASE_URL}/search", params, DEFAULT_TIMEOUT)
    except TimeoutError as exc:
        return {
            "ok": False,
            "query": query,
            "results": [],
            "error": {"type": "timeout", "message": str(exc), "status": 0},
        }
    except PermissionError as exc:
        return {
            "ok": False,
            "query": query,
            "results": [],
            "error": {"type": "permission_denied", "message": str(exc), "status": 0},
        }
    except RuntimeError as exc:
        return {
            "ok": False,
            "query": query,
            "results": [],
            "error": {"type": "request_error", "message": str(exc), "status": 0},
        }
    except ValueError as exc:
        return {
            "ok": False,
            "query": query,
            "results": [],
            "error": {"type": "parse_error", "message": str(exc), "status": 0},
        }

    if response["status"] != 200:
        return {
            "ok": False,
            "query": query,
            "results": [],
            "error": {"type": "http_error", "message": "HTTP error", "status": response["status"]},
        }

    data = response.get("data") or {}
    raw_results: List[Dict[str, Any]] = data.get("results") or []

    normalized_results = []
    for entry in raw_results:
        if len(normalized_results) >= clamped_results:
            break
        normalized_results.append(
            {
                "title": entry.get("title", ""),
                "url": entry.get("url", ""),
                "snippet": entry.get("content") or "",
                "engine": entry.get("engine") or "",
            }
        )

    result_payload = {
        "ok": True,
        "query": query,
        "results": normalized_results,
        "error": None,
    }
    _cache.set(cache_key, result_payload)
    return result_payload


__all__ = ["web_search"]
