from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("/{job_id}/{name}")
async def get_asset(job_id: str, name: str):
    path = Path("data/outputs") / job_id / "video" / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Asset not found.")
    return FileResponse(path)
