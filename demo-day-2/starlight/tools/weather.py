"""Weather tool: OpenWeather Current Weather API only (no mock fallback)."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from starlight.models import WeatherCondition

logger = logging.getLogger(__name__)


class WeatherUnavailableError(Exception):
    """Raised when OPENWEATHER_API_KEY is missing or the API request fails."""


def _parse_openweather(data: dict[str, Any]) -> WeatherCondition:
    clouds = float(data.get("clouds", {}).get("all", 0))
    rain = data.get("rain") or {}
    snow = data.get("snow") or {}
    precipitation = 0.0
    if isinstance(rain, dict):
        precipitation += float(rain.get("1h", 0) or rain.get("3h", 0) or 0)
    if isinstance(snow, dict):
        precipitation += float(snow.get("1h", 0) or snow.get("3h", 0) or 0)
    vis_m = data.get("visibility")
    if vis_m is None:
        visibility = "moderate"
    else:
        vis_m = float(vis_m)
        if vis_m >= 8000:
            visibility = "good"
        elif vis_m >= 4000:
            visibility = "moderate"
        else:
            visibility = "poor"
    temp = float(data.get("main", {}).get("temp", 12.0))
    score = int(max(0, min(100, 100 - clouds * 0.65 - min(40.0, precipitation * 15))))
    return WeatherCondition(
        cloud_cover=clouds,
        precipitation=precipitation,
        visibility=visibility,
        temperature=temp,
        observation_score=score,
    )


def fetch_weather(
    date: str,
    time: str,
    latitude: float,
    longitude: float,
) -> tuple[WeatherCondition, str]:
    """
    Fetch current weather at (latitude, longitude) via OpenWeather API.

    ``date`` and ``time`` are accepted for API symmetry with the rest of the agent;
    OpenWeather Current Weather does not use them (no historical lookup on free tier).

    Raises:
        WeatherUnavailableError: Missing API key or HTTP/network/parsing failure.
    """
    del date, time  # Current Weather API is "now"; kept for caller signature compatibility.

    api_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        raise WeatherUnavailableError(
            "OPENWEATHER_API_KEY가 설정되어 있어야 합니다. (목 날씨는 사용하지 않습니다.)"
        )

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": latitude, "lon": longitude, "appid": api_key, "units": "metric"}
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        return _parse_openweather(data), "OpenWeather Current Weather API"
    except Exception as e:
        logger.warning("Weather API failed: %s", e)
        raise WeatherUnavailableError(f"날씨 API 호출 실패: {e}") from e
