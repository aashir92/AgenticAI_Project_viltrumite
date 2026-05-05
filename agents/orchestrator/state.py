from __future__ import annotations

from typing import TypedDict


class OrchestratorState(TypedDict):
    job_id: str
    user_prompt: str
    story_spec_path: str
    timing_manifest_path: str
    master_audio_path: str
    final_video_path: str
