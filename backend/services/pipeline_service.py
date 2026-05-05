from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
from uuid import uuid4

from agents.orchestrator.graph import build_pipeline_graph
from backend.websocket.manager import ConnectionManager
from shared.utils import setup_logger, write_json


class PipelineService:
    def __init__(self, ws_manager: ConnectionManager) -> None:
        self.ws = ws_manager
        self.logger = setup_logger("pipeline-service")
        self.jobs: Dict[str, Dict] = {}

    async def _emit(self, job_id: str, phase: str, status: str, percent: int, meta: Dict) -> None:
        payload = {"phase": phase, "status": status, "percent": percent, "meta": meta}
        self.jobs[job_id]["events"].append(payload)
        await self.ws.broadcast(job_id, payload)

    async def run_job(self, job_id: str) -> None:
        state = self.jobs[job_id]
        try:
            loop = asyncio.get_running_loop()
            graph = build_pipeline_graph(
                progress_cb=lambda phase, status, percent, meta: asyncio.run_coroutine_threadsafe(
                    self._emit(job_id, phase, status, percent, meta), loop
                )
            )
            out = await graph.ainvoke({"job_id": job_id, "user_prompt": state["user_prompt"]})
            state["status"] = "completed"
            state["final_video_path"] = out.get("final_video_path")
            await self._emit(job_id, "done", "completed", 100, {"final_video_path": state["final_video_path"]})
        except Exception as exc:
            self.logger.exception("Job %s failed: %s", job_id, exc)
            state["status"] = "failed"
            state["error"] = str(exc)
            await self._emit(job_id, "error", "failed", 100, {"error": str(exc)})
        finally:
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            write_json(Path("data/outputs") / job_id / "job_state.json", state)

    def start_job(self, user_prompt: str) -> str:
        job_id = uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        self.jobs[job_id] = {"job_id": job_id, "user_prompt": user_prompt, "status": "running", "events": [], "created_at": now}
        asyncio.create_task(self.run_job(job_id))
        return job_id

    def get_job(self, job_id: str) -> Dict:
        if job_id not in self.jobs:
            raise KeyError("Job not found")
        return self.jobs[job_id]
