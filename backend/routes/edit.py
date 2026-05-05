from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agents.edit_agent.agent import EditAgent
from shared.schemas import EditRequest

router = APIRouter(prefix="/api/edit", tags=["edit"])
edit_agent = EditAgent()


@router.post("/{job_id}")
async def apply_edit(job_id: str, req: EditRequest):
    try:
        return edit_agent.apply(job_id, req.query)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{job_id}/undo")
async def undo_edit(job_id: str):
    try:
        return edit_agent.undo(job_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
