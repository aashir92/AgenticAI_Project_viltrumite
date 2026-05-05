from __future__ import annotations

from typing import Any, Dict

from mcp.base_tool import BaseTool
from state_manager.state_manager import StateManager


class StateTool(BaseTool):
    name = "state_tool"
    description = "Persist and recover state snapshots."

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        manager = StateManager()
        action = kwargs["action"]
        job_id = kwargs["job_id"]
        if action == "snapshot":
            version = manager.snapshot(job_id=job_id, state=kwargs["state"], note=kwargs.get("note", ""))
            return {"version": version}
        if action == "undo":
            restored = manager.undo(job_id)
            return {"state": restored}
        if action == "latest":
            latest = manager.latest(job_id)
            return {"state": latest}
        raise ValueError(f"Unsupported action: {action}")
