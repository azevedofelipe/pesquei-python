"""Open-Meteo weather + sunrise/sunset lookup.

Open-Meteo (https://open-meteo.com) is free with no API key required and no
metered/paid tier — confirmed directly against the live API while building
this integration (see the backend-dev report for the confirming `curl`
calls). Its docs confirm a single call's `daily` block can return
`sunrise`/`sunset` alongside weather variables, so this module makes exactly
one HTTP call per lookup — no separate sunrise/sunset API is needed.

Two Open-Meteo endpoints are used depending on how far `when` is from today:
- `api.open-meteo.com/v1/forecast` — recent past (~last 90 days) and
  near-future dates; Open-Meteo's "good first integration."
- `archive-api.open-meteo.com/v1/archive` — historical reanalysis data for
  older dates the forecast endpoint rejects with a 400 (its supported window
  is a rolling ~90-day-back/~16-day-forward range around today).

This module tries the forecast endpoint first and falls back to the archive
endpoint on failure, so callers don't need to reason about which one applies
to a given `date_caught`.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime

import httpx

from clients.http import build_async_client

logger = logging.getLogger(__name__)

FORECAST_BASE_URL = "https://api.open-meteo.com"
ARCHIVE_BASE_URL = "https://archive-api.open-meteo.com"

_HOURLY_VARS = "temperature_2m,weathercode"
_DAILY_VARS = "sunrise,sunset"

# WMO weather interpretation codes, per Open-Meteo's docs
# (https://open-meteo.com/en/docs) — used to turn a numeric `weathercode`
# into a short human-readable label for `Catch.conditions`.
_WEATHER_CODE_LABELS: dict[int, str] = {
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


@dataclass
class WeatherSnapshot:
    temperature: float | None
    conditions: str | None
    sunrise: datetime | None
    sunset: datetime | None


def _weather_code_label(code: int | None) -> str | None:
    if code is None:
        return None
    return _WEATHER_CODE_LABELS.get(code, f"Unknown (WMO code {code})")


def _params(latitude: float, longitude: float, target_date: date) -> dict:
    iso_date = target_date.isoformat()
    return {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": iso_date,
        "end_date": iso_date,
        "hourly": _HOURLY_VARS,
        "daily": _DAILY_VARS,
        # Requested explicitly as UTC so the returned hourly/daily
        # timestamps line up with how this app already stores
        # `Catch.date_caught` as a naive datetime (see AGENTS.md's Known
        # issues entry on that column's timezone ambiguity) — we're
        # matching the app's existing convention here, not fixing it.
        "timezone": "UTC",
    }


async def _fetch(base_url: str, path: str, params: dict) -> dict:
    async with build_async_client(base_url) as client:
        response = await client.get(path, params=params)
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise ValueError(data.get("reason", "Open-Meteo returned an error"))
        response.raise_for_status()
        return data


def _closest_hourly_reading(data: dict, when: datetime) -> tuple[float | None, int | None]:
    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    codes = hourly.get("weathercode") or []

    if not times:
        return None, None

    best_index = 0
    best_diff: float | None = None
    for index, time_str in enumerate(times):
        try:
            candidate = datetime.fromisoformat(time_str)
        except ValueError:
            continue
        diff = abs((candidate - when).total_seconds())
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_index = index

    temperature = temps[best_index] if best_index < len(temps) else None
    code = codes[best_index] if best_index < len(codes) else None
    return temperature, code


def _daily_sun_times(data: dict) -> tuple[datetime | None, datetime | None]:
    daily = data.get("daily") or {}
    sunrise_list = daily.get("sunrise") or []
    sunset_list = daily.get("sunset") or []

    sunrise = datetime.fromisoformat(sunrise_list[0]) if sunrise_list else None
    sunset = datetime.fromisoformat(sunset_list[0]) if sunset_list else None
    return sunrise, sunset


async def get_weather_snapshot(
    latitude: float, longitude: float, when: datetime
) -> WeatherSnapshot | None:
    """Look up temperature/conditions/sunrise/sunset for a given location and
    time via Open-Meteo.

    Returns `None` (after logging a warning) on any failure — network error,
    timeout, or an unparseable response from *both* endpoints. Callers should
    treat this as a best-effort nice-to-have snapshot, never a reason to fail
    the caller's own operation (e.g. catch creation).
    """
    params = _params(latitude, longitude, when.date())

    try:
        data = await _fetch(FORECAST_BASE_URL, "/v1/forecast", params)
    except (httpx.HTTPError, ValueError) as exc:
        logger.info(
            "Open-Meteo forecast lookup failed for (%s, %s) on %s, falling back to archive: %s",
            latitude, longitude, when.date(), exc,
        )
        try:
            data = await _fetch(ARCHIVE_BASE_URL, "/v1/archive", params)
        except (httpx.HTTPError, ValueError) as archive_exc:
            logger.warning(
                "Open-Meteo archive lookup also failed for (%s, %s) on %s: %s",
                latitude, longitude, when.date(), archive_exc,
            )
            return None

    try:
        temperature, code = _closest_hourly_reading(data, when)
        sunrise, sunset = _daily_sun_times(data)
    except Exception:
        logger.warning(
            "Failed to parse Open-Meteo response for (%s, %s) on %s",
            latitude, longitude, when.date(),
            exc_info=True,
        )
        return None

    return WeatherSnapshot(
        temperature=temperature,
        conditions=_weather_code_label(code),
        sunrise=sunrise,
        sunset=sunset,
    )
