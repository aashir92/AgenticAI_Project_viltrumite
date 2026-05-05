from __future__ import annotations

from pathlib import Path

from shared.utils import ensure_dir


class Storage:
    def __init__(self, root: str = "data/state_versions") -> None:
        self.root = ensure_dir(root)

    def job_dir(self, job_id: str) -> Path:
        return ensure_dir(self.root / job_id)
