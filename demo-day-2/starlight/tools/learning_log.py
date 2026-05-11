"""Append-only learning log (optional Tool)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from starlight.models import LearningLogEntry

DEFAULT_LOG_PATH = Path(os.environ.get("STARLIGHT_LOG_PATH", "data/starlight_learning.jsonl"))


def append_learning_log(entry: LearningLogEntry, path: Path | None = None) -> Path:
    log_path = path or DEFAULT_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        **entry.model_dump(),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path
