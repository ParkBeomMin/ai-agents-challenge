"""별빛탐구 — location-based astronomy learning agent."""

from __future__ import annotations

__all__ = ["build_graph"]


def __getattr__(name: str):
    if name == "build_graph":
        from starlight.graph import build_graph

        return build_graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
