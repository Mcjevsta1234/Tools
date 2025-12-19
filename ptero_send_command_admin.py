"""Open WebUI tool to send admin-only console commands via Pterodactyl Client API.

This tool validates caller context for the ADMIN role, preserves the command
exactly as provided (after safety checks), logs every invocation for auditing,
and delegates execution to `ptero_client` with structured, JSON-serializable
responses. No caching is applied because command execution must reflect
real-time state.

Security & validation:
- user_context must include roles (list[str]) and discord_id (str); roles must
  contain ADMIN (case-insensitive comparison).
- Commands must be length 1..500 and must not contain null bytes. Command text
  is never trimmed or modified.
- server_id must be a non-empty string of reasonable length.
- All calls are appended to /app/backend/data/ptero_audit.log with timestamp,
  discord_id, server_id, and command.
- HTTP calls are performed by ptero_client with explicit timeouts and
  allowlisted base URLs.

Returns a dict:
{
  "ok": bool,
  "server_id": str,
  "command": str,
  "executed_by": str,
  "result": {...} | None,
  "error": null | {"type": str, "message": str}
}
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from ptero_client import PteroClient

TOOL_DESCRIPTION = "Execute admin-only Pterodactyl console commands with audit logging."
TOOL_EXAMPLES = {
    "correct": [
        "ptero_send_command_admin('server123', 'say Hello', {'roles': ['ADMIN'], 'discord_id': '42'})",
    ],
    "incorrect": [
        "ptero_send_command_admin('server123', '', {'roles': ['ADMIN'], 'discord_id': '42'})",
        "ptero_send_command_admin('server123', 'say hi', {'roles': ['USER'], 'discord_id': '42'})",
    ],
}

AUDIT_LOG_PATH = "/app/backend/data/ptero_audit.log"


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
    """Validate the command string without altering its content."""

    if not isinstance(command, str):
        raise ValueError("command must be a string")
    if "\x00" in command:
        raise ValueError("command contains null bytes")
    if len(command) == 0:
        raise ValueError("command must be non-empty")
    if len(command) > 500:
        raise ValueError("command is too long")
    return command


def _normalize_roles(roles: Any) -> List[str]:
    """Validate roles as a list of strings and normalize to uppercase."""

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
    """Validate user_context payload and require ADMIN role."""

    if not isinstance(user_context, dict):
        raise ValueError("user_context must be a dict")

    roles_raw = user_context.get("roles")
    discord_id = user_context.get("discord_id")

    roles = _normalize_roles(roles_raw)
    if "ADMIN" not in roles:
        raise PermissionError("user lacks ADMIN role")

    if not isinstance(discord_id, str) or not discord_id.strip():
        raise ValueError("discord_id must be a non-empty string")

    return {"roles": roles, "discord_id": discord_id.strip()}


def _append_audit_log(discord_id: str, server_id: str, command: str) -> None:
    """Append audit entry; failures are silent to avoid leaking errors to users."""

    try:
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        line = f"{timestamp} discord_id={discord_id} server_id={server_id} command={command}\n"
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(line)
    except Exception:
        # Intentionally swallow exceptions to prevent audit issues from
        # impacting command execution; no secrets are written.
        return


def ptero_send_command_admin(server_id: str, command: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Send arbitrary console commands to a Pterodactyl server for admins only.

    Args:
        server_id: Pterodactyl server identifier.
        command: Console command text (1..500 chars, no null bytes).
        user_context: Dict containing roles (list[str]) and discord_id (str).

    Returns:
        JSON-serializable dict with execution status and audit metadata.

    Raises:
        ValueError: For invalid inputs.
        PermissionError: For missing ADMIN role.
    """

    normalized_server = _normalize_server_id(server_id)
    normalized_command = _normalize_command(command)
    try:
        validated_context = _validate_user_context(user_context)
    except PermissionError as exc:
        _append_audit_log(user_context.get("discord_id", ""), normalized_server, normalized_command)
        return {
            "ok": False,
            "server_id": normalized_server,
            "command": normalized_command,
            "executed_by": str(user_context.get("discord_id", "")),
            "result": None,
            "error": {"type": "permission", "message": str(exc)},
        }

    _append_audit_log(validated_context["discord_id"], normalized_server, normalized_command)

    client = PteroClient()
    send_result = client.send_console_command(normalized_server, normalized_command)

    ok = bool(send_result.get("ok"))
    error_obj = None if ok else {"type": "command_error", "message": str(send_result.get("error"))}

    return {
        "ok": ok,
        "server_id": normalized_server,
        "command": normalized_command,
        "executed_by": validated_context["discord_id"],
        "result": send_result,
        "error": error_obj,
    }
