"""
Pterodactyl Client API helper for Open WebUI tools.

This module provides a minimal, deterministic wrapper around the Pterodactyl
Client API for sending console commands, restarting servers, retrieving console
output, and interacting with the file system. All functions validate inputs,
respect an allowlisted base URL, use explicit request timeouts, and return
JSON-serializable dictionaries with structured error details.

Environment variables:
- PTERO_BASE_URL: Base URL of the Pterodactyl panel (default "https://panel.example.com").
- PTERO_CLIENT_API_KEY: API token for the Client API (required).
- PTERO_TIMEOUT_SECONDS: Timeout applied to connect/read operations (default 10).
- PTERO_CACHE_TTL_SECONDS: TTL in seconds for cacheable endpoints (default 30).

Security:
- Only allow requests to the configured base URL.
- Prevent directory traversal via normalize_path.
- No secrets are printed; inputs are validated and exceptions raised for misuse.
"""
import os
import posixpath
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

DEFAULT_BASE_URL = os.environ.get("PTERO_BASE_URL", "https://panel.example.com").rstrip("/")
DEFAULT_TIMEOUT = float(os.environ.get("PTERO_TIMEOUT_SECONDS", "10"))
DEFAULT_CACHE_TTL = int(os.environ.get("PTERO_CACHE_TTL_SECONDS", "30"))
ALLOWED_BASE_URLS = {DEFAULT_BASE_URL}


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


class PteroClientError(Exception):
    """Custom exception for internal error handling."""


class PteroClient:
    """Minimal Pterodactyl Client API wrapper for Open WebUI tools."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: Optional[float] = None) -> None:
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        if self.base_url not in ALLOWED_BASE_URLS:
            raise PermissionError("Base URL not in allowlist")
        self.api_key = api_key or os.environ.get("PTERO_CLIENT_API_KEY") or ""
        if not self.api_key.strip():
            raise ValueError("PTERO_CLIENT_API_KEY is required")
        self.timeout = timeout or DEFAULT_TIMEOUT
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

    def send_console_command(self, server_id: str, command: str) -> Dict[str, Any]:
        self._validate_server(server_id)
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must be a non-empty string")
        payload = {"command": command.strip()}
        return self._post(f"/api/client/servers/{server_id}/command", payload)

    def get_console_output(self, server_id: str) -> Dict[str, Any]:
        self._validate_server(server_id)
        cache_key = ("console_output", server_id)
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached
        result = self._get(f"/api/client/servers/{server_id}/resources")
        if result.get("ok"):
            _cache.set(cache_key, result)
        return result

    def restart_server(self, server_id: str) -> Dict[str, Any]:
        self._validate_server(server_id)
        payload = {"signal": "restart"}
        return self._post(f"/api/client/servers/{server_id}/power", payload)

    def list_files(self, server_id: str, path: str) -> Dict[str, Any]:
        self._validate_server(server_id)
        normalized_path = normalize_path(path)
        cache_key = ("list_files", server_id, normalized_path)
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached
        result = self._get(
            f"/api/client/servers/{server_id}/files/list",
            params={"directory": normalized_path},
        )
        if result.get("ok"):
            _cache.set(cache_key, result)
        return result

    def download_file(self, server_id: str, path: str) -> Dict[str, Any]:
        self._validate_server(server_id)
        normalized_path = normalize_path(path)
        cache_key = ("download", server_id, normalized_path)
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached
        response = self._get(
            f"/api/client/servers/{server_id}/files/download",
            params={"file": normalized_path},
            allow_follow=True,
        )
        if response.get("ok"):
            _cache.set(cache_key, response)
        return response

    def _post(self, path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        url = self._build_url(path)
        try:
            resp = requests.post(
                url,
                json=json_body,
                headers=self._headers(),
                timeout=(self.timeout, self.timeout),
            )
        except requests.exceptions.Timeout:
            return {"ok": False, "data": None, "error": {"type": "timeout", "message": "Request timed out", "status": 0}}
        except requests.RequestException as exc:
            return {"ok": False, "data": None, "error": {"type": "request_error", "message": str(exc), "status": 0}}

        return self._parse_response(resp)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, allow_follow: bool = False) -> Dict[str, Any]:
        url = self._build_url(path)
        try:
            resp = requests.get(
                url,
                params=params,
                headers=self._headers(),
                timeout=(self.timeout, self.timeout),
            )
        except requests.exceptions.Timeout:
            return {"ok": False, "data": None, "error": {"type": "timeout", "message": "Request timed out", "status": 0}}
        except requests.RequestException as exc:
            return {"ok": False, "data": None, "error": {"type": "request_error", "message": str(exc), "status": 0}}

        if allow_follow and resp.status_code == 200:
            parsed_json = self._safe_json(resp)
            if parsed_json is not None:
                attributes = parsed_json.get("attributes") or {}
                download_url = attributes.get("url")
                if download_url:
                    return self._follow_download(download_url)
            return self._parse_response(resp, expect_json=False)

        return self._parse_response(resp)

    def _follow_download(self, download_url: str) -> Dict[str, Any]:
        if not isinstance(download_url, str) or not download_url:
            return {"ok": False, "data": None, "error": {"type": "parse_error", "message": "Missing download URL", "status": 0}}
        parsed = urlparse(download_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in ALLOWED_BASE_URLS:
            return {"ok": False, "data": None, "error": {"type": "permission_denied", "message": "Download URL not allowed", "status": 0}}
        try:
            resp = requests.get(download_url, timeout=(self.timeout, self.timeout))
        except requests.exceptions.Timeout:
            return {"ok": False, "data": None, "error": {"type": "timeout", "message": "Download timed out", "status": 0}}
        except requests.RequestException as exc:
            return {"ok": False, "data": None, "error": {"type": "request_error", "message": str(exc), "status": 0}}
        if resp.status_code != 200:
            return {"ok": False, "data": None, "error": {"type": "http_error", "message": "HTTP error", "status": resp.status_code}}
        return {"ok": True, "data": resp.text, "error": None}

    def _parse_response(self, response: requests.Response, expect_json: bool = True) -> Dict[str, Any]:
        status = response.status_code
        if status != 200:
            return {"ok": False, "data": None, "error": {"type": "http_error", "message": "HTTP error", "status": status}}
        if not expect_json:
            return {"ok": True, "data": response.text, "error": None}
        parsed_json = self._safe_json(response)
        if parsed_json is None:
            return {"ok": False, "data": None, "error": {"type": "parse_error", "message": "Invalid JSON", "status": status}}
        data = parsed_json.get("attributes") or parsed_json
        return {"ok": True, "data": data, "error": None}

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _build_url(self, path: str) -> str:
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("path must start with '/'")
        return f"{self.base_url}{path}"

    def _validate_server(self, server_id: str) -> None:
        if not isinstance(server_id, str) or not server_id.strip():
            raise ValueError("server_id must be a non-empty string")
        if len(server_id) > 100:
            raise ValueError("server_id is too long")

    @staticmethod
    def _safe_json(response: requests.Response) -> Optional[Dict[str, Any]]:
        try:
            return response.json()
        except ValueError:
            return None


def normalize_path(path: str) -> str:
    """Normalize and validate a file path to prevent traversal."""

    if not isinstance(path, str) or not path:
        raise ValueError("path must be a non-empty string")
    cleaned = path.strip()
    if ".." in cleaned.split("/"):
        raise PermissionError("Path traversal not allowed")
    normalized = posixpath.normpath(cleaned)
    if normalized.startswith(".."):
        raise PermissionError("Path traversal not allowed")
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    return normalized


def is_path_allowed(path: str, allowlist: Optional[str] = None) -> bool:
    """Check whether a given normalized path is within an allowlist prefix."""

    normalized = normalize_path(path)
    prefix = normalize_path(allowlist) if allowlist else "/"
    return normalized.startswith(prefix)
