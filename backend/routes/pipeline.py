from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.pipeline_service import PipelineService

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class StartRequest(BaseModel):
    prompt: str


def get_router(service: PipelineService) -> APIRouter:
    @router.post("/start")
    async def start(req: StartRequest):
        if not req.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt is required.")
        return {"job_id": service.start_job(req.prompt)}

    @router.get("/{job_id}")
    async def status(job_id: str):
        try:
            return service.get_job(job_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Job not found.")

    return router
