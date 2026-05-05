from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from shared.utils import read_json, write_json


class History:
    def __init__(self, history_path: Path) -> None:
        self.path = history_path
        if not self.path.exists():
            write_json(self.path, {"versions": []})

    def list_versions(self) -> List[Dict]:
        return read_json(self.path)["versions"]

    def append(self, entry: Dict) -> None:
        payload = read_json(self.path)
        payload["versions"].append(entry)
        write_json(self.path, payload)

    def pop(self) -> Dict:
        payload = read_json(self.path)
        if not payload["versions"]:
            raise ValueError("No versions to pop.")
        item = payload["versions"].pop()
        write_json(self.path, payload)
        return item
