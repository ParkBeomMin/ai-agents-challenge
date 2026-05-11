"""CLI entry for 별빛탐구 (Starlight Explorer)."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from starlight.graph import build_graph
from starlight.models import ObservationInput
from starlight.timeutil import resolve_observation_wall_clock

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "WARNING"))
load_dotenv()


def main() -> None:
    p = argparse.ArgumentParser(description="별빛탐구 — 위치·시간 기반 천문 학습 에이전트")
    p.add_argument("--date", default=None, help="YYYY-MM-DD (생략 시 관측지 로컬 ‘지금’ 또는 아래 규칙)")
    p.add_argument("--time", default=None, help="HH:MM 24h (생략 시 관측지 로컬 ‘지금’ 또는 21:00)")
    p.add_argument("--lat", type=float, required=True, help="위도")
    p.add_argument("--lon", type=float, required=True, help="경도")
    args = p.parse_args()

    date_s, time_s = resolve_observation_wall_clock(args.date, args.time, args.lat, args.lon)
    inp = ObservationInput(date=date_s, time=time_s, latitude=args.lat, longitude=args.lon)
    graph = build_graph()
    result = graph.invoke({"observation_input": inp})
    print(result.get("final_answer", "(출력 없음)"))
    if result.get("pipeline_error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
