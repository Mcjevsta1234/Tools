"""
Open WebUI tool that checks the status of a Minecraft Java server via mcsrvstat.us.

The `minecraft_status` function validates input, applies TTL caching, and performs
an allowlisted HTTP request with explicit timeouts. It returns normalized JSON
including player counts, version, MOTD, and small extra metadata when available.
Configuration is sourced from environment variables; errors are surfaced in a
structured, JSON-serializable shape. Secrets are never logged.

Examples:
    Correct: ``minecraft_status("play.example.com:25565")``
    Incorrect: ``minecraft_status("")``
"""
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

TOOL_DESCRIPTION = "Check if a Minecraft Java server is online and summarize its status."
TOOL_EXAMPLES = {
    "correct": [
        "minecraft_status('play.example.com')",
        "minecraft_status('mc.example.net:25565')",
    ],
    "incorrect": [
        "minecraft_status('')",
        "minecraft_status('a'*300)",
    ],
}

ALLOWED_BASE_URLS = {"https://api.mcsrvstat.us"}
DEFAULT_TIMEOUT = float(os.environ.get("MC_STATUS_TIMEOUT_SECONDS", "8"))
DEFAULT_CACHE_TTL = int(os.environ.get("MC_STATUS_CACHE_TTL_SECONDS", "60"))

CACHE_TTL_SECONDS = DEFAULT_CACHE_TTL
API_BASE = "https://api.mcsrvstat.us/2"


class TTLCache:
    """A minimal in-memory TTL cache for deterministic single-process use."""

    def __init__(self, ttl_seconds: int) -> None:
        if not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")
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


_cache = TTLCache(CACHE_TTL_SECONDS)


def _normalize_server(server_ip: str) -> str:
    """Normalize the server input for validation and caching."""

    if not isinstance(server_ip, str):
        raise ValueError("server_ip must be a string")
    normalized = server_ip.strip()
    if not normalized:
        raise ValueError("server_ip must be non-empty")
    if len(normalized) > 255:
        raise ValueError("server_ip must be 255 characters or fewer")
    return normalized


def _http_get_json(url: str, timeout: float) -> Dict[str, Any]:
    """Perform an allowlisted HTTP GET request and parse JSON response.

    Args:
        url: Full request URL. Must be in the ALLOWED_BASE_URLS set.
        timeout: Timeout in seconds applied to connect and read.

    Returns:
        A dict containing status and parsed JSON data, or error details.

    Raises:
        PermissionError: If URL base is not allowlisted.
        TimeoutError: If the request times out.
        RuntimeError: For non-timeout request errors.
        ValueError: When JSON parsing fails for 200 responses.
    """

    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base not in ALLOWED_BASE_URLS:
        raise PermissionError("URL not allowed by policy")

    try:
        response = requests.get(url, timeout=(timeout, timeout))
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


def _flatten_motd(motd: Any) -> str:
    """Flatten MOTD fields into a single string."""

    if not motd:
        return ""
    if isinstance(motd, dict):
        parts = motd.get("clean") or motd.get("raw") or []
    elif isinstance(motd, list):
        parts = motd
    else:
        return str(motd)
    return " ".join([str(p).strip() for p in parts if str(p).strip()])


def _parse_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize mcsrvstat.us payload into tool response fields."""

    online = bool(payload.get("online"))
    result: Dict[str, Any] = {
        "ok": True,
        "online": online,
        "players": {"online": 0, "max": 0},
        "version": "",
        "motd": "",
        "extra": {},
    }

    if not online:
        return result

    players = payload.get("players") or {}
    software = payload.get("software")
    plugins = payload.get("plugins")
    mods = payload.get("mods")

    result["players"] = {
        "online": int(players.get("online", 0) or 0),
        "max": int(players.get("max", 0) or 0),
    }
    result["version"] = str(payload.get("version") or "")
    result["motd"] = _flatten_motd(payload.get("motd"))

    extra: Dict[str, Any] = {}
    if software:
        extra["software"] = str(software)
    if plugins and isinstance(plugins, list):
        extra["plugin_count"] = len(plugins)
    if mods and isinstance(mods, list):
        extra["mod_count"] = len(mods)
    if extra:
        result["extra"] = extra
    else:
        result.pop("extra", None)

    return result


def minecraft_status(server_ip: str) -> Dict[str, Any]:
    """Retrieve Minecraft server status via mcsrvstat.us.

    Args:
        server_ip: Host or host:port of the server. Must be non-empty and <=255 chars.

    Returns:
        JSON-serializable dict with server status fields and structured error info.

    Raises:
        ValueError: For invalid input parameters.
        PermissionError: If outbound URL is disallowed.
        TimeoutError: On HTTP timeout.
        RuntimeError: On unexpected request failure.
    """

    normalized = _normalize_server(server_ip)
    cache_key = normalized
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{API_BASE}/{normalized}"
    try:
        response = _http_get_json(url, timeout=DEFAULT_TIMEOUT)
    except TimeoutError as exc:
        return {
            "ok": False,
            "server": normalized,
            "online": False,
            "players": {"online": 0, "max": 0},
            "version": "",
            "motd": "",
            "error": {"type": "timeout", "message": str(exc)},
            "extra": {},
        }
    except PermissionError:
        # Explicitly re-raise to surface policy violations clearly.
        raise
    except RuntimeError as exc:
        return {
            "ok": False,
            "server": normalized,
            "online": False,
            "players": {"online": 0, "max": 0},
            "version": "",
            "motd": "",
            "error": {"type": "http_error", "message": str(exc)},
            "extra": {},
        }
    except ValueError as exc:
        return {
            "ok": False,
            "server": normalized,
            "online": False,
            "players": {"online": 0, "max": 0},
            "version": "",
            "motd": "",
            "error": {"type": "parse_error", "message": str(exc)},
            "extra": {},
        }

    status_code = response.get("status")
    data = response.get("data")
    if status_code != 200 or data is None:
        return {
            "ok": False,
            "server": normalized,
            "online": False,
            "players": {"online": 0, "max": 0},
            "version": "",
            "motd": "",
            "error": {"type": "http_error", "message": "Unexpected HTTP status", "status": status_code},
            "extra": {},
        }

    parsed = _parse_status(data)
    parsed["server"] = normalized
    parsed.setdefault("error", None)

    _cache.set(cache_key, parsed)
    return parsed


__all__ = ["minecraft_status"]
