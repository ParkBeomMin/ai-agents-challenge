"""Local civil time at an observation site → UTC (shared by weather and sky tools)."""

from __future__ import annotations

import logging
from datetime import date, datetime, time as dtime, timezone

from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)


def local_wall_time_to_utc(date_str: str, time_str: str, lat: float, lon: float) -> datetime:
    """Interpret date + HH:MM as local wall time at (lat, lon); return UTC instant."""
    d = date.fromisoformat(date_str)
    parts = time_str.split(":")
    hh = int(parts[0])
    mm = int(parts[1]) if len(parts) > 1 else 0
    local_wall = dtime(hh, mm)
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=lon, lat=lat)
    if tz_name:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(tz_name)
        local = datetime.combine(d, local_wall, tzinfo=tz)
        return local.astimezone(timezone.utc)
    logger.warning(
        "timezonefinder returned no zone for lat=%.4f lon=%.4f; treating input time as UTC.",
        lat,
        lon,
    )
    return datetime.combine(d, local_wall, tzinfo=timezone.utc)


def observer_local_now(lat: float, lon: float) -> datetime:
    """Current instant as aware datetime in the observer's civil timezone (lat/lon)."""
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=lon, lat=lat)
    utc_now = datetime.now(timezone.utc)
    if tz_name:
        from zoneinfo import ZoneInfo

        return utc_now.astimezone(ZoneInfo(tz_name))
    logger.warning(
        "timezonefinder returned no zone for lat=%.4f lon=%.4f; using UTC for 'now'.",
        lat,
        lon,
    )
    return utc_now.astimezone(timezone.utc)


def resolve_observation_wall_clock(
    date_arg: str | None,
    time_arg: str | None,
    lat: float,
    lon: float,
) -> tuple[str, str]:
    """
    Fill missing CLI date/time for sky geometry.

    - Both omitted: observer-local now (wall clock at lat/lon).
    - Date only: that date at 21:00 local (evening default).
    - Time only: today's date (observer-local) at that time.
    """
    now_local = observer_local_now(lat, lon)
    if date_arg is None and time_arg is None:
        return now_local.date().isoformat(), now_local.strftime("%H:%M")
    if date_arg is None:
        assert time_arg is not None
        return now_local.date().isoformat(), time_arg
    if time_arg is None:
        return date_arg, "21:00"
    return date_arg, time_arg
