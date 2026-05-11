"""Fetch star coordinates from VizieR (Hipparcos I/239) via astroquery — no embedded RA/Dec in app code."""

from __future__ import annotations

import logging
from functools import lru_cache

from astropy.table import Table, vstack
from astroquery.vizier import Vizier

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _vizier() -> Vizier:
    v = Vizier(columns=["HIP", "Vmag", "_RA.icrs", "_DE.icrs"])
    v.ROW_LIMIT = 50
    return v


@lru_cache(maxsize=16)
def fetch_hip_stars(hip_ids: tuple[int, ...]) -> Table:
    """Return a single astropy Table with RA/Dec in degrees for each HIP (queries VizieR over the network)."""
    tables: list[Table] = []
    v = _vizier()
    for hip in hip_ids:
        try:
            res = v.query_constraints(catalog="I/239/hip_main", HIP=str(hip))
            if len(res) > 0 and len(res[0]) > 0:
                tables.append(res[0])
        except Exception as e:
            logger.warning("VizieR query failed for HIP %s: %s", hip, e)
    if not tables:
        return Table()
    return vstack(tables, metadata_conflicts="silent")
