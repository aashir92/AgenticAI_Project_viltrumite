from __future__ import annotations

from shared.schemas import EditIntent


def build_edit_plan(intent: EditIntent) -> dict:
    rerender_required = intent.target in {"video_frame", "video", "audio", "script"}
    return {
        "intent": intent.intent,
        "target": intent.target,
        "params": intent.params,
        "rerender_required": rerender_required,
    }
