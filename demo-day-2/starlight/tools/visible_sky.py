"""Visible sky: AstronomyAPI (solar system, HTTPS) + VizieR Hipparcos + Skyfield (geometry only)."""

from __future__ import annotations

import logging
import math
import os
from datetime import datetime, timezone
from typing import Literal

from skyfield.api import Star, load, wgs84
from skyfield.magnitudelib import planetary_magnitude
from starlight.models import SkyObject
from starlight.timeutil import local_wall_time_to_utc
from starlight.tools.astronomy_api import astronomy_api_configured, fetch_solar_system_positions
from starlight.tools.vizier_catalog import fetch_hip_stars

logger = logging.getLogger(__name__)

ObservationMode = Literal["good", "moderate", "indoor"]

# Korean label, Hipparcos HIP id, default learner difficulty (before horizon tweak).
# Coordinates are resolved at runtime from VizieR I/239 — not stored here as RA/Dec.
_ANCHOR_HIP: list[tuple[str, int, str]] = [
    ("오리온자리", 27989, "보통"),
    ("카시오페이아자리", 3179, "쉬움"),
    ("북두칠성", 54061, "쉬움"),
    ("백조자리", 102098, "보통"),
    ("거문고자리", 91262, "쉬움"),
    ("페가수스자리", 113881, "보통"),
    ("안드로메다자리", 677, "보통"),
    ("레오자리", 49669, "보통"),
    ("처녀자리", 65474, "보통"),
    ("목동자리", 69673, "쉬움"),
    ("큰개자리", 32349, "쉬움"),
    ("난아자리", 97649, "쉬움"),
    ("물고기자리", 7097, "어려움"),
]

_PLANETS: list[tuple[str, str]] = [
    ("수성", "mercury"),
    ("금성", "venus"),
    ("화성", "mars"),
    ("목성", "jupiter barycenter"),
    ("토성", "saturn barycenter"),
    ("천왕성", "uranus barycenter"),
    ("해왕성", "neptune barycenter"),
]


def _azimuth_to_direction(az_deg: float) -> str:
    sectors = ["북쪽", "북동쪽", "동쪽", "남동쪽", "남쪽", "남서쪽", "서쪽", "북서쪽"]
    x = (float(az_deg) + 360.0) % 360.0
    idx = int((x + 22.5) % 360.0 // 45.0) % 8
    return sectors[idx]


def _difficulty_from_mag(vmag: float, near_horizon: bool, default: str) -> str:
    if default != "보통":
        return default
    if math.isnan(vmag):
        return "보통"
    if near_horizon:
        return "어려움"
    if vmag <= 1.5:
        return "쉬움"
    if vmag <= 4.0:
        return "보통"
    return "어려움"


def _planet_difficulty(name: str, mag: float) -> str:
    if math.isnan(mag):
        if name in ("천왕성", "해왕성"):
            return "어려움"
        return "보통"
    if mag <= -1.0:
        return "쉬움"
    if mag <= 2.5:
        return "쉬움"
    if mag <= 5.0:
        return "보통"
    return "어려움"


def _include_for_mode(
    mode: ObservationMode,
    *,
    altitude_deg: float,
    magnitude: float,
    is_moon: bool,
    is_planet: bool,
    anchor_vmag: float | None,
) -> bool:
    if mode in ("good", "indoor"):
        return altitude_deg > 0.0
    if altitude_deg <= 0.0:
        return False
    if is_moon:
        return True
    if is_planet:
        return not math.isnan(magnitude) and magnitude <= 4.5
    if anchor_vmag is not None:
        return altitude_deg >= 20.0 or anchor_vmag <= 2.0
    return altitude_deg >= 25.0


def _observer_elevation_m() -> float:
    try:
        return float(os.environ.get("OBSERVER_ELEVATION_M", "0"))
    except ValueError:
        return 0.0


def _solar_from_skyfield(
    utc_dt: datetime,
    latitude: float,
    longitude: float,
    mode: ObservationMode,
) -> list[SkyObject]:
    ts = load.timescale()
    eph = load("de421.bsp")
    t = ts.from_datetime(utc_dt)
    earth = eph["earth"]
    observer = earth + wgs84.latlon(latitude_degrees=latitude, longitude_degrees=longitude)
    out: list[SkyObject] = []

    moon = eph["moon"]
    ast_m = observer.at(t).observe(moon)
    alt_m, az_m, _ = ast_m.apparent().altaz("standard")
    if _include_for_mode(
        mode,
        altitude_deg=alt_m.degrees,
        magnitude=float("nan"),
        is_moon=True,
        is_planet=False,
        anchor_vmag=None,
    ):
        out.append(
            SkyObject(
                name="달",
                object_type="위성",
                direction=_azimuth_to_direction(az_m.degrees),
                difficulty="쉬움" if alt_m.degrees > 15.0 else "보통",
            )
        )

    for label, key in _PLANETS:
        body = eph[key]
        ast = observer.at(t).observe(body)
        alt, az, _ = ast.apparent().altaz("standard")
        try:
            mag = planetary_magnitude(ast)
        except (ValueError, TypeError):
            mag = float("nan")
        if not _include_for_mode(
            mode,
            altitude_deg=alt.degrees,
            magnitude=mag,
            is_moon=False,
            is_planet=True,
            anchor_vmag=None,
        ):
            continue
        near_hz = alt.degrees < 15.0
        diff = _planet_difficulty(label, mag)
        if near_hz and diff == "쉬움":
            diff = "보통"
        out.append(
            SkyObject(
                name=label,
                object_type="행성",
                direction=_azimuth_to_direction(az.degrees),
                difficulty=diff,
            )
        )
    return out


def _solar_from_astronomy_api(
    latitude: float,
    longitude: float,
    date_str: str,
    time_str: str,
    mode: ObservationMode,
) -> list[SkyObject]:
    elev = _observer_elevation_m()
    rows = fetch_solar_system_positions(latitude, longitude, elev, date_str, time_str)
    out: list[SkyObject] = []
    for row in rows:
        alt = row["altitude_deg"]
        az = row["azimuth_deg"]
        mag = row.get("magnitude")
        if mag is None:
            mag = float("nan")
        name = row["name_ko"]
        otype = row["object_type"]
        is_moon = name == "달"
        if not _include_for_mode(
            mode,
            altitude_deg=alt,
            magnitude=mag,
            is_moon=is_moon,
            is_planet=not is_moon,
            anchor_vmag=None,
        ):
            continue
        if is_moon:
            diff = "쉬움" if alt > 15.0 else "보통"
        else:
            diff = _planet_difficulty(name, mag)
            if alt < 15.0 and diff == "쉬움":
                diff = "보통"
        out.append(
            SkyObject(
                name=name,
                object_type=otype,
                direction=_azimuth_to_direction(az),
                difficulty=diff,
            )
        )
    return out


def _stellar_from_vizier(
    utc_dt: datetime,
    latitude: float,
    longitude: float,
    mode: ObservationMode,
) -> list[SkyObject]:
    hips = tuple(h for _, h, _ in _ANCHOR_HIP)
    tbl = fetch_hip_stars(hips)
    if len(tbl) == 0:
        logger.warning("VizieR returned no stars for constellation anchors.")
        return []

    hip_to_meta = {h: (ko, df) for ko, h, df in _ANCHOR_HIP}
    hip_col = tbl["HIP"]
    ra_col = tbl["_RA.icrs"]
    de_col = tbl["_DE.icrs"]
    vmag_col = tbl["Vmag"]

    ts = load.timescale()
    t = ts.from_datetime(utc_dt)
    earth = load("de421.bsp")["earth"]
    observer = earth + wgs84.latlon(latitude_degrees=latitude, longitude_degrees=longitude)

    out: list[SkyObject] = []
    for i in range(len(tbl)):
        hip = int(hip_col[i])
        meta = hip_to_meta.get(hip)
        if meta is None:
            continue
        ko_name, default_diff = meta
        ra_deg = float(ra_col[i])
        dec_deg = float(de_col[i])
        vmag = float(vmag_col[i])
        star = Star(ra_hours=ra_deg / 15.0, dec_degrees=dec_deg)
        ast_s = observer.at(t).observe(star)
        alt_s, az_s, _ = ast_s.apparent().altaz("standard")
        if not _include_for_mode(
            mode,
            altitude_deg=alt_s.degrees,
            magnitude=float("nan"),
            is_moon=False,
            is_planet=False,
            anchor_vmag=vmag,
        ):
            continue
        near_hz = alt_s.degrees < 20.0
        diff = _difficulty_from_mag(vmag, near_hz, default_diff)
        if near_hz and diff == "쉬움":
            diff = "보통"
        out.append(
            SkyObject(
                name=ko_name,
                object_type="별자리",
                direction=_azimuth_to_direction(az_s.degrees),
                difficulty=diff,
            )
        )
    return out


def list_visible_objects(
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    mode: ObservationMode,
) -> list[SkyObject]:
    """
    Solar system: AstronomyAPI (REST) when credentials are set; otherwise Skyfield+DE421.

    Stars: VizieR Hipparcos catalog (network) for coordinates; Skyfield only projects alt/az.

    Requires internet on first use (DE421, VizieR; AstronomyAPI when configured).
    """
    utc_dt = local_wall_time_to_utc(date, time, latitude, longitude)

    solar: list[SkyObject] = []
    if astronomy_api_configured():
        try:
            solar = _solar_from_astronomy_api(latitude, longitude, date, time, mode)
        except Exception as e:
            logger.warning("AstronomyAPI failed (%s); falling back to Skyfield ephemeris.", e)
            solar = _solar_from_skyfield(utc_dt, latitude, longitude, mode)
    else:
        solar = _solar_from_skyfield(utc_dt, latitude, longitude, mode)

    stellar = _stellar_from_vizier(utc_dt, latitude, longitude, mode)

    candidates = solar + stellar

    _planet_rank = {
        "수성": 1,
        "금성": 2,
        "화성": 3,
        "목성": 4,
        "토성": 5,
        "천왕성": 6,
        "해왕성": 7,
    }

    def sort_key(o: SkyObject) -> tuple[int, int, str]:
        if o.name == "달":
            return (0, 0, o.name)
        if o.object_type == "행성":
            return (1, _planet_rank.get(o.name, 99), o.name)
        return (2, 0, o.name)

    candidates.sort(key=sort_key)

    seen: set[str] = set()
    unique: list[SkyObject] = []
    for o in candidates:
        if o.name in seen:
            continue
        seen.add(o.name)
        unique.append(o)
    return unique
