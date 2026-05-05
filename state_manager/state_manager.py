from __future__ import annotations

from pathlib import Path
from typing import Dict

from shared.utils import read_json, write_json

from .history import History
from .snapshot import Snapshot
from .storage import Storage


class StateManager:
    def __init__(self) -> None:
        self.storage = Storage()

    def _history(self, job_id: str) -> History:
        return History(self.storage.job_dir(job_id) / "history.json")

    def snapshot(self, job_id: str, state: Dict, note: str = "") -> int:
        history = self._history(job_id)
        version = len(history.list_versions()) + 1
        snap = Snapshot.create(version=version, state=state, note=note)
        state_path = self.storage.job_dir(job_id) / f"v_{version}.json"
        write_json(state_path, snap.state)
        history.append({"version": version, "timestamp": snap.timestamp, "note": note, "state_path": str(state_path)})
        return version

    def latest(self, job_id: str) -> Dict:
        versions = self._history(job_id).list_versions()
        if not versions:
            raise ValueError("No snapshot exists for job.")
        return read_json(versions[-1]["state_path"])

    def undo(self, job_id: str) -> Dict:
        history = self._history(job_id)
        versions = history.list_versions()
        if len(versions) < 2:
            raise ValueError("No previous version to revert to.")
        history.pop()
        prev = history.list_versions()[-1]
        return read_json(prev["state_path"])
