"""
Tooling utilities for parsing Minecraft Spark TPS output.

Functions:
    parse_spark_tps(console_text: str) -> dict
        Extracts minimum and average TPS values from Spark console output.

Purpose:
    Provide deterministic parsing of Spark-reported TPS values for Open WebUI tools.
    Enforces input validation, structured JSON-serializable responses, and
    simple in-memory caching with TTL to avoid repeated parsing of identical
    console logs.

  Security considerations:
      - Validates inputs to prevent misuse (requires non-empty string input).
      - Avoids executing shell commands or accessing external systems.
      - Returns only JSON-serializable dictionaries.

  Examples:
      Correct: ``parse_spark_tps("[22:19:33] TPS from last 5s,10s,1m: 19.95, 19.98, 19.99")``
      Incorrect: ``parse_spark_tps("")``
  """
from __future__ import annotations

import hashlib
import os
import re
import time
from typing import Dict, Optional

TOOL_DESCRIPTION = "Parse Spark TPS output and extract min/avg values."
TOOL_EXAMPLES = {
    "correct": [
        "parse_spark_tps('[Server thread/INFO]: TPS: 19.9')",
    ],
    "incorrect": [
        "parse_spark_tps('')",
        "parse_spark_tps(123)",
    ],
}


class TTLCache:
    """In-memory TTL cache with string keys.

    Args:
        default_ttl (int): Time-to-live in seconds applied to new entries.

    The cache stores values alongside their expiry timestamps. Expired entries
    are ignored on retrieval. This is intentionally simple and in-memory only.
    """

    def __init__(self, default_ttl: int) -> None:
        if default_ttl <= 0:
            raise ValueError("default_ttl must be positive")
        self._default_ttl = default_ttl
        self._store: Dict[str, tuple[float, dict]] = {}

    def get(self, key: str) -> Optional[dict]:
        now = time.time()
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if expires_at <= now:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        use_ttl = ttl if ttl is not None else self._default_ttl
        if use_ttl <= 0:
            raise ValueError("ttl must be positive")
        expires_at = time.time() + use_ttl
        self._store[key] = (expires_at, value)


def _get_cache() -> TTLCache:
    ttl_seconds = int(os.environ.get("MC_PARSE_CACHE_TTL_SECONDS", "300"))
    return TTLCache(ttl_seconds)


_CACHE = _get_cache()


def _normalize_text(text: str) -> str:
    return text.strip()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _find_tps_values(console_text: str) -> tuple[Optional[float], Optional[float]]:
    lines = [line for line in console_text.splitlines() if "tps" in line.lower()]
    labeled_pattern = re.compile(r"(?i)(min(?:imum)?|avg|average)[^\d]{0,5}(\d+(?:\.\d+)?)")
    pair_pattern = re.compile(
        r"(\d+(?:\.\d+)?)\s*[\/,]\s*(\d+(?:\.\d+)?)\s*(?:tps|TPS)",
        re.IGNORECASE,
    )
    number_pattern = re.compile(r"\d+(?:\.\d+)?")

    min_val: Optional[float] = None
    avg_val: Optional[float] = None

    for line in lines:
        for label, value in labeled_pattern.findall(line):
            numeric = float(value)
            if label.lower().startswith("min") and min_val is None:
                min_val = numeric
            if label.lower().startswith("avg") and avg_val is None:
                avg_val = numeric

        if min_val is None or avg_val is None:
            pair_match = pair_pattern.search(line)
            if pair_match:
                first, second = pair_match.groups()
                if min_val is None:
                    min_val = float(first)
                if avg_val is None:
                    avg_val = float(second)

        if min_val is None or avg_val is None:
            numbers = number_pattern.findall(line)
            if numbers:
                if avg_val is None:
                    avg_val = float(numbers[0])
                if len(numbers) > 1 and min_val is None:
                    min_val = float(numbers[1])

        if min_val is not None and avg_val is not None:
            break

    return min_val, avg_val


def parse_spark_tps(console_text: str) -> dict:
    """Parse Spark console output and extract TPS values.

    Args:
        console_text (str): Raw console output from Spark TPS command.

    Returns:
        dict: JSON-serializable result containing TPS statistics or structured
        errors when not found.

    Raises:
        ValueError: If the input is not a non-empty string.
    """

    if not isinstance(console_text, str):
        raise ValueError("console_text must be a string")
    normalized = _normalize_text(console_text)
    if not normalized:
        raise ValueError("console_text cannot be empty")

    cache_key = _hash_text(normalized)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    min_tps, avg_tps = _find_tps_values(normalized)
    if min_tps is None and avg_tps is None:
        result = {"ok": False, "tps": {"min": None, "avg": None}, "error": {"type": "not_found", "message": "No TPS found"}}
    else:
        result = {"ok": True, "tps": {"min": min_tps, "avg": avg_tps}, "error": None}

    _CACHE.set(cache_key, result)
    return result


__all__ = ["parse_spark_tps"]
