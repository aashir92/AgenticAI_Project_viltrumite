from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict


@dataclass
class Snapshot:
    version: int
    timestamp: str
    note: str
    state: Dict

    @staticmethod
    def create(version: int, state: Dict, note: str = "") -> "Snapshot":
        return Snapshot(version=version, timestamp=datetime.now(timezone.utc).isoformat(), note=note, state=state)
