"""
Open WebUI tools for listing and reading Pterodactyl server files with strict admin enforcement.

Tools:
- ptero_list_files(server_id: str, path: str, user_context: dict) -> dict
- ptero_read_file(server_id: str, path: str, user_context: dict) -> dict

Security & behavior:
- Requires user_context.roles to include "ADMIN"; otherwise returns permission errors.
- Enforces path allowlist for base directories (/logs, /crash-reports, /config) and prevents traversal.
- Normalizes paths via ptero_client.normalize_path and clamps file responses to 512KB with truncation flag.
- Uses environment-configured timeouts and TTL caching; all HTTP calls are performed by the allowlisted
  ptero_client wrapper with connect/read timeouts.
- Returns JSON-serializable dicts only; inputs are validated and errors are structured.

Examples:
    Correct: ``ptero_list_files("server123", "/logs", {"roles":["ADMIN"],"discord_id":"42"})``
    Incorrect: ``ptero_read_file("server123", "../../etc/passwd", {"roles":["ADMIN"],"discord_id":"42"})``
"""
import os
import time
from typing import Any, Dict, Iterable, Optional, Tuple

import ptero_client

TOOL_DESCRIPTIONS = {
    "ptero_list_files": "List admin-allowed directories for a Pterodactyl server.",
    "ptero_read_file": "Read small admin-approved files from a Pterodactyl server.",
}
TOOL_EXAMPLES = {
    "ptero_list_files": {
        "correct": [
            "ptero_list_files('server123', '/logs', {'roles': ['ADMIN'], 'discord_id': '42'})",
        ],
        "incorrect": [
            "ptero_list_files('server123', '../../etc', {'roles': ['ADMIN'], 'discord_id': '42'})",
            "ptero_list_files('server123', '/logs', {'roles': ['USER'], 'discord_id': '42'})",
        ],
    },
    "ptero_read_file": {
        "correct": [
            "ptero_read_file('server123', '/logs/latest.log', {'roles': ['ADMIN'], 'discord_id': '42'})",
        ],
        "incorrect": [
            "ptero_read_file('server123', '/config/../secret', {'roles': ['ADMIN'], 'discord_id': '42'})",
            "ptero_read_file('server123', '/logs/latest.log', {'roles': ['USER'], 'discord_id': '42'})",
        ],
    },
}

MAX_BYTES = 524_288
DEFAULT_CACHE_TTL = int(os.environ.get("PTERO_FILES_CACHE_TTL_SECONDS", "30"))
ALLOWED_BASE_DIRS: Tuple[str, ...] = (
    "/logs",
    "/crash-reports",
    "/config",
)


class TTLCache:
    """A minimal TTL cache for JSON-serializable values."""

    def __init__(self, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._ttl = ttl_seconds
        self._store: Dict[Any, Any] = {}

    def get(self, key: Any) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.time() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: Any, value: Any) -> None:
        self._store[key] = (time.time() + self._ttl, value)


_cache = TTLCache(DEFAULT_CACHE_TTL)


def _is_admin(user_context: Dict[str, Any]) -> bool:
    roles = user_context.get("roles") if isinstance(user_context, dict) else None
    if not isinstance(roles, Iterable) or isinstance(roles, (str, bytes)):
        return False
    return "ADMIN" in set(str(r).strip().upper() for r in roles)


def _permission_error(message: str) -> Dict[str, Any]:
    return {"ok": False, "error": {"type": "permission", "message": message}}


def _disallowed_path_error(path: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "type": "disallowed_path",
            "message": f"Path '{path}' is not within allowed directories",
            "allowed": list(ALLOWED_BASE_DIRS),
        },
    }


def _ensure_allowed_path(path: str) -> str:
    normalized = ptero_client.normalize_path(path)
    if not any(normalized.startswith(base) for base in ALLOWED_BASE_DIRS):
        raise PermissionError(_disallowed_path_error(normalized)["error"]["message"])
    return normalized


def _client() -> ptero_client.PteroClient:
    return ptero_client.PteroClient()


def _cache_lookup(key: Any) -> Optional[Dict[str, Any]]:
    cached = _cache.get(key)
    if cached is not None:
        return cached
    return None


def _cache_store(key: Any, value: Dict[str, Any]) -> None:
    _cache.set(key, value)


def ptero_list_files(server_id: str, path: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    List files within an allowlisted directory on a Pterodactyl server.

    Inputs:
      - server_id: target server identifier (non-empty string, length <= 100).
      - path: directory path to list (must reside within ALLOWED_BASE_DIRS).
      - user_context: dict containing roles and discord_id; must include ADMIN role.

    Returns:
      JSON-serializable dict with ok flag, normalized path, file entries, and structured errors.
    """

    if not isinstance(server_id, str) or not server_id.strip() or len(server_id) > 100:
        raise ValueError("server_id must be a non-empty string up to 100 characters")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string")
    if not isinstance(user_context, dict):
        raise ValueError("user_context must be a dict")
    if not _is_admin(user_context):
        return _permission_error("ADMIN role required")

    try:
        normalized_path = _ensure_allowed_path(path)
    except PermissionError:
        return _disallowed_path_error(path)

    cache_key = ("list", server_id, normalized_path)
    cached = _cache_lookup(cache_key)
    if cached is not None:
        return cached

    client = _client()
    response = client.list_files(server_id, normalized_path)
    if not response.get("ok"):
        result = {
            "ok": False,
            "server_id": server_id,
            "path": normalized_path,
            "files": [],
            "error": response.get("error"),
        }
        _cache_store(cache_key, result)
        return result

    data = response.get("data") or {}
    entries = data.get("data") if isinstance(data, dict) else None
    files = []
    for item in entries or []:
        name = str(item.get("name", ""))
        if not name:
            continue
        is_file = bool(item.get("is_file", item.get("object") == "file"))
        size = item.get("size") if isinstance(item, dict) else None
        if size is None:
            size = item.get("bytes") if isinstance(item, dict) else None
        modified = (
            item.get("modified")
            or item.get("modified_at")
            or item.get("created_at")
            or ""
        )
        files.append(
            {
                "name": name,
                "is_file": is_file,
                "size": size if isinstance(size, (int, float)) else 0,
                "modified": str(modified),
            }
        )

    result = {
        "ok": True,
        "server_id": server_id,
        "path": normalized_path,
        "files": files,
        "error": None,
    }
    _cache_store(cache_key, result)
    return result


def ptero_read_file(server_id: str, path: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read a file from an allowlisted directory on a Pterodactyl server with size limits.

    Inputs:
      - server_id: target server identifier (non-empty string, length <= 100).
      - path: file path to read (must reside within ALLOWED_BASE_DIRS).
      - user_context: dict containing roles and discord_id; must include ADMIN role.

    Returns:
      JSON-serializable dict with ok flag, content (truncated to 512KB), truncation flag, and errors.
    """

    if not isinstance(server_id, str) or not server_id.strip() or len(server_id) > 100:
        raise ValueError("server_id must be a non-empty string up to 100 characters")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string")
    if not isinstance(user_context, dict):
        raise ValueError("user_context must be a dict")
    if not _is_admin(user_context):
        return _permission_error("ADMIN role required")

    try:
        normalized_path = _ensure_allowed_path(path)
    except PermissionError:
        return _disallowed_path_error(path)

    cache_key = ("read", server_id, normalized_path)
    cached = _cache_lookup(cache_key)
    if cached is not None:
        return cached

    client = _client()
    response = client.download_file(server_id, normalized_path)
    if not response.get("ok"):
        result = {
            "ok": False,
            "server_id": server_id,
            "path": normalized_path,
            "content": "",
            "truncated": False,
            "error": response.get("error"),
        }
        _cache_store(cache_key, result)
        return result

    raw_content = response.get("data")
    content_str = str(raw_content) if raw_content is not None else ""
    truncated = False
    if len(content_str.encode("utf-8")) > MAX_BYTES:
        # Truncate by bytes to avoid splitting multi-byte characters unpredictably.
        content_bytes = content_str.encode("utf-8")
        content_str = content_bytes[:MAX_BYTES].decode("utf-8", errors="ignore")
        truncated = True

    result = {
        "ok": True,
        "server_id": server_id,
        "path": normalized_path,
        "content": content_str,
        "truncated": truncated,
        "error": None,
    }
    _cache_store(cache_key, result)
    return result
