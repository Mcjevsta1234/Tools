"""Open WebUI tool to send limited console commands via Pterodactyl Client API.

This tool enforces a strict allowlist of safe commands for both regular users
and admins, validates caller context, and delegates execution to the
`ptero_client` module. Responses are JSON-serializable with structured error
objects. Optional short-lived console output retrieval is cached for a brief
TTL to reduce repeated requests.

Security & validation:
- user_context must include roles (list[str]) and discord_id (str); roles must
  contain USER or ADMIN.
- Commands must match the allowlist (case-insensitive, trimmed) exactly.
- server_id and command inputs are validated; no secrets are logged.
- HTTP calls are performed by ptero_client with explicit timeouts and
  allowlisted base URLs.

Environment variables:
- PTERO_OUTPUT_CACHE_TTL_SECONDS: TTL seconds for optional console output cache
  (default 3). Set to <=0 to disable caching.

Returns a dict:
{
  "ok": bool,
  "server_id": str,
  "command": str,
  "result": {...},
  "error": null | {"type": str, "message": str, "allowed"?: list}
}
"""
import os
import time
from typing import Any, Dict, List, Optional

from ptero_client import PteroClient

TOOL_DESCRIPTION = "Send allowlisted Pterodactyl console commands with user role checks."
TOOL_EXAMPLES = {
    "correct": [
        "ptero_send_command_limited('server123', 'spark tps', {'roles': ['USER'], 'discord_id': '42'})",
        "ptero_send_command_limited('server123', 'forge tps', {'roles': ['ADMIN'], 'discord_id': '42'})",
    ],
    "incorrect": [
        "ptero_send_command_limited('server123', 'rm -rf /', {'roles': ['USER'], 'discord_id': '42'})",
        "ptero_send_command_limited('', 'spark tps', {'roles': ['USER'], 'discord_id': '42'})",
    ],
}

ALLOWED_USER_COMMANDS = ["spark tps", "spark profiler", "forge tps"]
ALLOWED_COMMANDS_LOWER = {cmd.lower() for cmd in ALLOWED_USER_COMMANDS}
ALLOWED_ROLES = {"USER", "ADMIN"}

DEFAULT_CACHE_TTL = int(os.environ.get("PTERO_OUTPUT_CACHE_TTL_SECONDS", "3"))


class TTLCache:
    """A minimal in-memory TTL cache for deterministic single-process use."""

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


_output_cache: Optional[TTLCache] = None
if DEFAULT_CACHE_TTL > 0:
    try:
        _output_cache = TTLCache(DEFAULT_CACHE_TTL)
    except ValueError:
        _output_cache = None


def _normalize_server_id(server_id: str) -> str:
    """Validate and normalize server identifier."""

    if not isinstance(server_id, str):
        raise ValueError("server_id must be a string")
    cleaned = server_id.strip()
    if not cleaned:
        raise ValueError("server_id must be non-empty")
    if len(cleaned) > 100:
        raise ValueError("server_id is too long")
    return cleaned


def _normalize_command(command: str) -> str:
    """Validate and normalize the command string."""

    if not isinstance(command, str):
        raise ValueError("command must be a string")
    cleaned = command.strip()
    if not cleaned:
        raise ValueError("command must be non-empty")
    return cleaned


def _normalize_roles(roles: Any) -> List[str]:
    """Validate roles as a list of strings."""

    if not isinstance(roles, list):
        raise ValueError("roles must be a list of strings")
    normalized: List[str] = []
    for role in roles:
        if not isinstance(role, str):
            raise ValueError("roles must be a list of strings")
        role_clean = role.strip()
        if role_clean:
            normalized.append(role_clean.upper())
    return normalized


def _validate_user_context(user_context: Any) -> Dict[str, Any]:
    """Validate user_context payload and required roles."""

    if not isinstance(user_context, dict):
        raise ValueError("user_context must be a dict")

    roles_raw = user_context.get("roles")
    discord_id = user_context.get("discord_id")

    roles = _normalize_roles(roles_raw)
    if not roles:
        raise PermissionError("missing user roles")
    if not any(role in ALLOWED_ROLES for role in roles):
        raise PermissionError("user lacks required role")

    if not isinstance(discord_id, str) or not discord_id.strip():
        raise ValueError("discord_id must be a non-empty string")

    return {"roles": roles, "discord_id": discord_id.strip()}


def _is_command_allowed(command: str) -> bool:
    normalized = command.strip().lower()
    return normalized in ALLOWED_COMMANDS_LOWER


def _cache_console_output(server_id: str, data: Dict[str, Any]) -> None:
    if _output_cache:
        _output_cache.set(("console_output", server_id), data)


def _get_cached_console_output(server_id: str) -> Optional[Dict[str, Any]]:
    if not _output_cache:
        return None
    return _output_cache.get(("console_output", server_id))


def ptero_send_command_limited(server_id: str, command: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Send allowlisted console commands to a Pterodactyl server.

    Args:
        server_id: Pterodactyl server identifier.
        command: Console command text; must be in ALLOWED_USER_COMMANDS.
        user_context: Dict containing roles (list[str]) and discord_id (str).

    Returns:
        JSON-serializable dict with execution status and optional console output.

    Raises:
        ValueError: For invalid inputs.
        PermissionError: For missing/insufficient roles.
    """

    normalized_server = _normalize_server_id(server_id)
    normalized_command = _normalize_command(command)
    try:
        _validate_user_context(user_context)
    except PermissionError as exc:
        return {
            "ok": False,
            "server_id": normalized_server,
            "command": normalized_command,
            "result": None,
            "error": {"type": "permission", "message": str(exc)},
        }

    if not _is_command_allowed(normalized_command):
        return {
            "ok": False,
            "server_id": normalized_server,
            "command": normalized_command,
            "result": None,
            "error": {
                "type": "disallowed_command",
                "message": "Command is not permitted",
                "allowed": ALLOWED_USER_COMMANDS,
            },
        }

    client = PteroClient()
    send_result = client.send_console_command(normalized_server, normalized_command)

    if not send_result.get("ok"):
        return {
            "ok": False,
            "server_id": normalized_server,
            "command": normalized_command,
            "result": send_result,
            "error": send_result.get("error") or {"type": "unknown", "message": "Command failed"},
        }

    console_output: Optional[Dict[str, Any]] = _get_cached_console_output(normalized_server)
    if console_output is None:
        time.sleep(0.6)
        console_output = client.get_console_output(normalized_server)
        if console_output.get("ok"):
            _cache_console_output(normalized_server, console_output)

    combined_result = {"command": send_result, "console_output": console_output}

    return {
        "ok": True,
        "server_id": normalized_server,
        "command": normalized_command,
        "result": combined_result,
        "error": None,
    }


__all__ = ["ptero_send_command_limited", "ALLOWED_USER_COMMANDS"]
