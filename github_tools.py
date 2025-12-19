"""
Open WebUI tool for fetching text/code files from public GitHub repositories.

Functions:
    github_fetch_repo(repo_url: str, ref: str = "main", max_files: int = 50) -> dict

The tool validates repository URLs, enforces allowlisted hosts, clamps the
number of files to retrieve, and respects a maximum byte budget while pulling
file contents. It communicates with the GitHub REST API using optional token
authentication from the environment and returns structured, JSON-serializable
results. Errors are converted into structured objects instead of allowing raw
exceptions to propagate. Simple TTL-based in-memory caching reduces repeated
API calls for the same parameters.

Examples:
    Correct: ``github_fetch_repo("https://github.com/owner/repo", max_files=10)``
    Incorrect: ``github_fetch_repo("https://example.com/owner/repo", max_files=0)``

Security considerations:
- Only public repository URLs on github.com are allowed; private token contents
  are never printed.
- HTTP interactions use timeouts and a fixed allowlist of hosts.
- Paths are controlled by the GitHub API responses; no arbitrary shell
  execution occurs.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

TOOL_DESCRIPTION = "Fetch selected text files from a public GitHub repository."
TOOL_EXAMPLES = {
    "correct": [
        "github_fetch_repo('https://github.com/owner/repo', max_files=5)",
    ],
    "incorrect": [
        "github_fetch_repo('https://example.com/notgithub/repo', max_files=5)",
        "github_fetch_repo('https://github.com/owner/repo', max_files=5000)",
    ],
}


_ALLOWED_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".py",
    ".java",
    ".go",
    ".rs",
    ".html",
    ".css",
    ".scss",
    ".sh",
}

_ALLOWED_HOSTS = {"github.com", "api.github.com", "raw.githubusercontent.com"}

_DEFAULT_TIMEOUT = float(os.getenv("GITHUB_TIMEOUT_SECONDS", "10"))
_CACHE_TTL = int(os.getenv("GITHUB_CACHE_TTL_SECONDS", "3600"))
_MAX_TOTAL_BYTES = int(os.getenv("GITHUB_MAX_TOTAL_BYTES", str(2 * 1024 * 1024)))


class TTLCache:
    """Simple thread-safe TTL cache using an in-memory dict."""

    def __init__(self) -> None:
        self._data: Dict[str, Tuple[float, object]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[object]:
        now = time.time()
        with self._lock:
            value = self._data.get(key)
            if value is None:
                return None
            expires_at, payload = value
            if now >= expires_at:
                self._data.pop(key, None)
                return None
            return payload

    def set(self, key: str, value: object, ttl: int) -> None:
        expires_at = time.time() + ttl
        with self._lock:
            self._data[key] = (expires_at, value)


_cache = TTLCache()


class GitHubRepo:
    __slots__ = ("owner", "name", "ref")

    def __init__(self, owner: str, name: str, ref: str) -> None:
        self.owner = owner
        self.name = name
        self.ref = ref

    def api_tree_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.name}/git/trees/{self.ref}"

    def raw_base_url(self) -> str:
        return f"https://raw.githubusercontent.com/{self.owner}/{self.name}/{self.ref}"


class GitHubError(Exception):
    """Internal exception to unify error handling."""

    def __init__(self, err_type: str, message: str, status: Optional[int] = None) -> None:
        super().__init__(message)
        self.err_type = err_type
        self.status = status
        self.message = message


def _parse_repo_url(repo_url: str, ref: str) -> GitHubRepo:
    if not isinstance(repo_url, str) or not repo_url.strip():
        raise ValueError("repo_url must be a non-empty string")
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError("ref must be a non-empty string")
    parsed = urlparse(repo_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("repo_url must use http or https")
    if parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError("repo_url must point to github.com")
    path = parsed.path.rstrip("/")
    match = re.fullmatch(r"/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:\.git)?", path)
    if not match:
        raise ValueError("repo_url must be in the form https://github.com/owner/repo")
    owner, name = match.group(1), match.group(2)
    return GitHubRepo(owner, name, ref.strip())


def _clamp_max_files(max_files: int) -> int:
    if not isinstance(max_files, int):
        raise ValueError("max_files must be an integer")
    return max(1, min(200, max_files))


def _headers() -> Dict[str, str]:
    headers = {
        "User-Agent": "OpenWebUI-GitHubTool/1.0",
        "Accept": "application/vnd.github+json",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _http_get_json(url: str, params: Optional[dict] = None, timeout: float = _DEFAULT_TIMEOUT) -> dict:
    _enforce_allowlist(url)
    try:
        response = requests.get(url, params=params, headers=_headers(), timeout=timeout)
    except requests.Timeout as exc:  # pragma: no cover - network conditions
        raise GitHubError("timeout", f"Request timed out: {exc}") from exc
    except requests.RequestException as exc:  # pragma: no cover - network conditions
        raise GitHubError("http_error", f"Request failed: {exc}") from exc

    if response.status_code != 200:
        raise GitHubError("http_error", f"HTTP {response.status_code}", status=response.status_code)

    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise GitHubError("parse_error", "Invalid JSON response") from exc


def _http_get_text(url: str, timeout: float = _DEFAULT_TIMEOUT) -> str:
    _enforce_allowlist(url)
    try:
        response = requests.get(url, headers=_headers(), timeout=timeout)
    except requests.Timeout as exc:  # pragma: no cover - network conditions
        raise GitHubError("timeout", f"Request timed out: {exc}") from exc
    except requests.RequestException as exc:  # pragma: no cover - network conditions
        raise GitHubError("http_error", f"Request failed: {exc}") from exc

    if response.status_code != 200:
        raise GitHubError("http_error", f"HTTP {response.status_code}", status=response.status_code)
    return response.text


def _enforce_allowlist(url: str) -> None:
    host = urlparse(url).hostname
    if host not in _ALLOWED_HOSTS:
        raise PermissionError("Host not allowlisted")


def _is_allowed_file(path: str) -> bool:
    for ext in _ALLOWED_EXTENSIONS:
        if path.lower().endswith(ext):
            return True
    return False


def _fetch_tree(repo: GitHubRepo) -> dict:
    cache_key = f"tree:{repo.owner}:{repo.name}:{repo.ref}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    result = _http_get_json(repo.api_tree_url(), params={"recursive": 1}, timeout=_DEFAULT_TIMEOUT)
    _cache.set(cache_key, result, _CACHE_TTL)
    return result


def github_fetch_repo(repo_url: str, ref: str = "main", max_files: int = 50) -> dict:
    """
    Fetch a set of text/code files from a public GitHub repository reference.

    Args:
        repo_url: HTTPS URL of the GitHub repository (e.g., https://github.com/owner/repo).
        ref: Branch, tag, or commit SHA to fetch from. Defaults to "main".
        max_files: Maximum number of files to retrieve (1..200), defaults to 50.

    Returns:
        A JSON-serializable dict with repository metadata, selected files and their
        contents, a truncated indicator if limits were hit, and structured errors on
        failure.
    """

    try:
        repo = _parse_repo_url(repo_url, ref)
        max_files_clamped = _clamp_max_files(max_files)
    except (ValueError, PermissionError) as exc:
        return {
            "ok": False,
            "repo": None,
            "files": [],
            "truncated": False,
            "error": {"type": "validation", "message": str(exc)},
        }

    cache_key = f"fetch:{repo.owner}:{repo.name}:{repo.ref}:{max_files_clamped}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        tree_data = _fetch_tree(repo)
        tree_entries = tree_data.get("tree", []) if isinstance(tree_data, dict) else []
        selected: List[dict] = []
        total_bytes = 0
        truncated = False

        for node in tree_entries:
            if node.get("type") != "blob":
                continue
            path = node.get("path", "")
            if not _is_allowed_file(path):
                continue
            file_url = f"{repo.raw_base_url()}/{path}"
            try:
                content_text = _http_get_text(file_url, timeout=_DEFAULT_TIMEOUT)
            except GitHubError as exc:
                return _error_response(repo, exc)

            content_bytes = content_text.encode("utf-8", errors="replace")
            projected_total = total_bytes + len(content_bytes)
            if projected_total > _MAX_TOTAL_BYTES:
                truncated = True
                break

            selected.append({"path": path, "content": content_text})
            total_bytes = projected_total

            if len(selected) >= max_files_clamped:
                truncated = len(selected) < len([n for n in tree_entries if n.get("type") == "blob" and _is_allowed_file(n.get("path", ""))])
                break

        result = {
            "ok": True,
            "repo": {"owner": repo.owner, "name": repo.name, "ref": repo.ref},
            "files": selected,
            "truncated": truncated,
            "error": None,
        }
        _cache.set(cache_key, result, _CACHE_TTL)
        return result
    except GitHubError as exc:
        return _error_response(repo, exc)
    except Exception as exc:  # pragma: no cover - unforeseen errors
        return _error_response(repo, GitHubError("unknown", f"Unexpected error: {exc}"))


def _error_response(repo: GitHubRepo, exc: GitHubError) -> dict:
    return {
        "ok": False,
        "repo": {"owner": repo.owner, "name": repo.name, "ref": repo.ref},
        "files": [],
        "truncated": False,
        "error": {"type": exc.err_type, "message": exc.message, "status": exc.status},
    }


__all__ = ["github_fetch_repo"]
