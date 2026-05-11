"""AstronomyAPI (https://astronomyapi.com) — solar system positions over HTTPS."""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE = "https://api.astronomyapi.com/api/v2/bodies/positions"

# Skip Sun — not a night-sky observation target for this agent.
_BODY_KO: dict[str, tuple[str, str] | None] = {
    "sun": None,
    "moon": ("달", "위성"),
    "mercury": ("수성", "행성"),
    "venus": ("금성", "행성"),
    "mars": ("화성", "행성"),
    "jupiter": ("목성", "행성"),
    "saturn": ("토성", "행성"),
    "uranus": ("천왕성", "행성"),
    "neptune": ("해왕성", "행성"),
}


def astronomy_api_configured() -> bool:
    app_id = os.environ.get("ASTRONOMY_API_APPLICATION_ID", "").strip()
    secret = os.environ.get("ASTRONOMY_API_APPLICATION_SECRET", "").strip()
    return bool(app_id and secret)


def _auth_header() -> str:
    app_id = os.environ["ASTRONOMY_API_APPLICATION_ID"].strip()
    secret = os.environ["ASTRONOMY_API_APPLICATION_SECRET"].strip()
    token = base64.b64encode(f"{app_id}:{secret}".encode()).decode("ascii")
    return f"Basic {token}"


def fetch_solar_system_positions(
    latitude: float,
    longitude: float,
    elevation_m: float,
    date_str: str,
    time_str: str,
) -> list[dict[str, Any]]:
    """
    Call AstronomyAPI positions endpoint (all bodies, rows format).

    Returns a list of dicts: name_ko, object_type, altitude_deg, azimuth_deg, body_id, magnitude (optional).
    Only entries with altitude > 0 are returned (above mathematical horizon).
    """
    if not astronomy_api_configured():
        raise RuntimeError("AstronomyAPI credentials missing (ASTRONOMY_API_APPLICATION_ID / SECRET).")

    # Pad time to HH:MM:SS if needed
    parts = time_str.split(":")
    hh, mm = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
    time_fmt = f"{hh:02d}:{mm:02d}:00"

    params = {
        "latitude": str(latitude),
        "longitude": str(longitude),
        "elevation": str(int(elevation_m)),
        "from_date": date_str,
        "to_date": date_str,
        "time": time_fmt,
    }
    headers = {"Authorization": _auth_header()}
    with httpx.Client(timeout=30.0) as client:
        r = client.get(BASE, params=params, headers=headers)
        r.raise_for_status()
        payload = r.json()

    return _parse_positions_payload(payload)


def _parse_horizontal_cell(pos_block: dict[str, Any]) -> tuple[float, float] | None:
    hor = pos_block.get("horizontal") or pos_block.get("horizonal") or {}
    alt_o = hor.get("altitude") or {}
    az_o = hor.get("azimuth") or {}
    try:
        alt = float(alt_o.get("degrees", "nan"))
        az = float(az_o.get("degrees", "nan"))
    except (TypeError, ValueError):
        return None
    return alt, az


def _parse_positions_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Support both `output=rows` layout and default tabular `table` layout."""
    data = payload.get("data") or {}
    out: list[dict[str, Any]] = []

    raw_rows = data.get("rows")
    if isinstance(raw_rows, list) and raw_rows:
        for row in raw_rows:
            body = row.get("body") or {}
            bid = (body.get("id") or "").lower()
            mapping = _BODY_KO.get(bid)
            if mapping is None:
                continue
            name_ko, otype = mapping
            positions = row.get("positions") or []
            if not positions:
                continue
            pos0 = positions[0]
            pos_block = pos0.get("position") or {}
            hz = _parse_horizontal_cell(pos_block)
            if hz is None:
                continue
            alt, az = hz
            if alt <= 0.0:
                continue
            mag = None
            extra = pos0.get("extraInfo") or {}
            if "magnitude" in extra:
                try:
                    mag = float(extra["magnitude"])
                except (TypeError, ValueError):
                    mag = None
            out.append(
                {
                    "body_id": bid,
                    "name_ko": name_ko,
                    "object_type": otype,
                    "altitude_deg": alt,
                    "azimuth_deg": az,
                    "magnitude": mag,
                }
            )
        return out

    table = data.get("table") or {}
    body_rows = table.get("rows") or []
    for row in body_rows:
        entry = row.get("entry") or {}
        bid = (entry.get("id") or "").lower()
        mapping = _BODY_KO.get(bid)
        if mapping is None:
            continue
        name_ko, otype = mapping
        cells = row.get("cells") or []
        if not cells:
            continue
        pos0 = cells[0]
        pos_block = pos0.get("position") or {}
        hz = _parse_horizontal_cell(pos_block)
        if hz is None:
            continue
        alt, az = hz
        if alt <= 0.0:
            continue
        mag = None
        extra = pos0.get("extraInfo") or {}
        if "magnitude" in extra:
            try:
                mag = float(extra["magnitude"])
            except (TypeError, ValueError):
                mag = None
        out.append(
            {
                "body_id": bid,
                "name_ko": name_ko,
                "object_type": otype,
                "altitude_deg": alt,
                "azimuth_deg": az,
                "magnitude": mag,
            }
        )
    return out
