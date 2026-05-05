from __future__ import annotations

from pathlib import Path
from typing import Dict

from shared.utils import read_json, write_json


class EditExecutor:
    def execute(self, job_id: str, plan: Dict) -> Dict:
        job_state_path = Path("data/outputs") / job_id / "job_state.json"
        if not job_state_path.exists():
            raise ValueError("Job state not found.")
        state = read_json(job_state_path)
        state.setdefault("edits", []).append(plan)
        state["last_edit_target"] = plan["target"]
        write_json(job_state_path, state)
        return state
