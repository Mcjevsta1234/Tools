"""
Open WebUI tool that returns current weather conditions for a provided location
using the Open-Meteo APIs.

The `weather_now` function validates inputs, uses TTL caching, and performs
geocoding followed by a forecast lookup to produce a normalized JSON payload.
Configuration (timeouts, cache TTL) is sourced from environment variables with
sane defaults. HTTP requests are guarded by an allowlist and explicit timeouts;
structured errors are returned for all failure cases. This module avoids
printing secrets, disallows arbitrary hosts, and raises clear exceptions for
invalid inputs.

Examples:
    Correct: ``weather_now("London")``
    Incorrect: ``weather_now("")``
"""
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests


TOOL_DESCRIPTION = "Fetch current weather for a location via Open-Meteo."
TOOL_EXAMPLES = {
    "correct": [
        "weather_now('London')",
        "weather_now('New York')",
    ],
    "incorrect": [
        "weather_now('')",
        "weather_now(123)",
    ],
}


ALLOWED_BASE_URLS = {
    "https://geocoding-api.open-meteo.com",
    "https://api.open-meteo.com",
}
DEFAULT_TIMEOUT = float(os.environ.get("WEATHER_TIMEOUT_SECONDS", "10"))
DEFAULT_CACHE_TTL = int(os.environ.get("WEATHER_CACHE_TTL_SECONDS", "300"))

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


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


_cache = TTLCache(DEFAULT_CACHE_TTL)


def _normalize_location(location: str) -> str:
    """Normalize a location string for caching and validation."""

    if not isinstance(location, str):
        raise ValueError("location must be a string")
    stripped = location.strip()
    if not stripped:
        raise ValueError("location must be a non-empty string")
    return " ".join(stripped.split()).lower()


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


def _parse_geocode(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract geocoding details from API response."""

    results = data.get("results") or []
    if not results:
        raise LookupError("Location not found")
    entry = results[0]
    return {
        "name": entry.get("name", ""),
        "country": entry.get("country", ""),
        "region": entry.get("admin1", ""),
        "lat": entry.get("latitude"),
        "lon": entry.get("longitude"),
    }


def _parse_current_weather(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract current weather details from API response."""

    current = data.get("current") or {}
    weather_code = current.get("weather_code")
    condition = WEATHER_CODE_MAP.get(weather_code, "Unknown")
    return {
        "time": current.get("time", ""),
        "temperature_c": current.get("temperature_2m"),
        "feels_like_c": current.get("apparent_temperature"),
        "precip_mm": current.get("precipitation"),
        "wind_kph": current.get("wind_speed_10m"),
        "wind_dir_deg": current.get("wind_direction_10m"),
        "condition": condition,
    }


def weather_now(location: str) -> Dict[str, Any]:
    """Return current weather conditions for the given location.

    Args:
        location: Human-readable location string. Must be non-empty.

    Returns:
        A JSON-serializable dictionary with keys:
            ok (bool): True when data is successfully retrieved.
            location (dict): Location metadata including query, name, region,
                country, coordinates, and timezone.
            current (dict): Current weather observations.
            error (dict|None): Structured error details when ok is False.

    Raises:
        ValueError: If the provided location is invalid.
    """

    normalized = _normalize_location(location)

    cached = _cache.get(normalized)
    if cached is not None:
        return cached

    geocode_params = {
        "name": normalized,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    try:
        geocode_response = _http_get_json(GEOCODE_URL, geocode_params, DEFAULT_TIMEOUT)
    except TimeoutError as exc:
        return {"ok": False, "error": {"type": "timeout", "message": str(exc)}}
    except PermissionError as exc:
        return {"ok": False, "error": {"type": "permission_denied", "message": str(exc)}}
    except RuntimeError as exc:
        return {"ok": False, "error": {"type": "request_error", "message": str(exc)}}
    except ValueError as exc:
        return {"ok": False, "error": {"type": "parse_error", "message": str(exc)}}

    if geocode_response["status"] != 200:
        return {"ok": False, "error": {"type": "http_error", "message": "HTTP error", "status": geocode_response["status"]}}

    geocode_data = geocode_response.get("data") or {}
    try:
        geo = _parse_geocode(geocode_data)
    except LookupError as exc:
        return {"ok": False, "error": {"type": "not_found", "message": str(exc)}}

    forecast_params = {
        "latitude": geo["lat"],
        "longitude": geo["lon"],
        "current": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m,wind_direction_10m,weather_code",
        "timezone": "auto",
    }

    try:
        forecast_response = _http_get_json(FORECAST_URL, forecast_params, DEFAULT_TIMEOUT)
    except TimeoutError as exc:
        return {"ok": False, "error": {"type": "timeout", "message": str(exc)}}
    except PermissionError as exc:
        return {"ok": False, "error": {"type": "permission_denied", "message": str(exc)}}
    except RuntimeError as exc:
        return {"ok": False, "error": {"type": "request_error", "message": str(exc)}}
    except ValueError as exc:
        return {"ok": False, "error": {"type": "parse_error", "message": str(exc)}}

    if forecast_response["status"] != 200:
        return {"ok": False, "error": {"type": "http_error", "message": "HTTP error", "status": forecast_response["status"]}}

    forecast_data = forecast_response.get("data") or {}
    current = _parse_current_weather(forecast_data)

    payload = {
        "ok": True,
        "location": {
            "query": location,
            "name": geo.get("name", ""),
            "region": geo.get("region", ""),
            "country": geo.get("country", ""),
            "lat": geo.get("lat"),
            "lon": geo.get("lon"),
            "timezone": forecast_data.get("timezone", ""),
        },
        "current": current,
        "error": None,
    }

    _cache.set(normalized, payload)
    return payload


__all__ = ["weather_now"]
