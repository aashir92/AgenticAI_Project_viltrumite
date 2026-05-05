from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, HTTPException

from agents.edit_agent.agent import EditAgent, EditAgentState
from shared.schemas import EditRequest

router = APIRouter(prefix="/api/edit", tags=["edit"])

# Lazy-initialised: created on first request so GROQ_API_KEY is loaded by then
_agent: EditAgent | None = None

# Per-job undo state stores — keyed by job_id
_job_states: Dict[str, EditAgentState] = {}


def _get_agent() -> EditAgent:
    global _agent
    if _agent is None:
        _agent = EditAgent()
    return _agent


def _get_state(job_id: str) -> EditAgentState:
    if job_id not in _job_states:
        _job_states[job_id] = EditAgentState({"job_id": job_id}, job_id=job_id)
    return _job_states[job_id]


@router.post("/{job_id}")
async def apply_edit(job_id: str, req: EditRequest):
    try:
        agent = _get_agent()
        state = _get_state(job_id)
        result = agent.handle(req.query, state)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{job_id}/undo")
async def undo_edit(job_id: str):
    try:
        agent = _get_agent()
        state = _get_state(job_id)
        result = agent.handle("undo", state)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
