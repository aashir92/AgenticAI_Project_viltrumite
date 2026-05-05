from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class CharacterSpec(BaseModel):
    name: str
    voice_personality: str
    visual_traits: str


class DialogueLine(BaseModel):
    speaker: str
    text: str
    emotion: str = "neutral"


class SceneSpec(BaseModel):
    scene_id: str
    title: str
    visual_description: str
    duration_seconds: int = Field(ge=6, le=25)
    dialogue: List[DialogueLine]


class StorySpec(BaseModel):
    story: str
    theme: str
    characters: List[CharacterSpec] = Field(min_length=2, max_length=2)
    scenes: List[SceneSpec] = Field(min_length=3, max_length=8)

    @model_validator(mode="after")
    def validate_runtime_and_characters(self) -> "StorySpec":
        total_duration = sum(scene.duration_seconds for scene in self.scenes)
        if total_duration < 50 or total_duration > 70:
            raise ValueError("Total duration must be approximately 1 minute (50-70s).")
        character_names = {c.name for c in self.characters}
        if len(character_names) != 2:
            raise ValueError("Exactly two unique characters are required.")
        for scene in self.scenes:
            for line in scene.dialogue:
                if line.speaker not in character_names:
                    raise ValueError(f"Unknown speaker '{line.speaker}' in scene {scene.scene_id}")
        return self


class TimingEntry(BaseModel):
    scene_id: str
    speaker: str
    text: str
    audio_file: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)

    @field_validator("end_ms")
    @classmethod
    def validate_end(cls, value: int, info: Any) -> int:
        start = info.data.get("start_ms", 0)
        if value <= start:
            raise ValueError("end_ms must be greater than start_ms.")
        return value


class TimingManifest(BaseModel):
    entries: List[TimingEntry]
    total_duration_ms: int = Field(ge=1)


class PipelineProgress(BaseModel):
    phase: Literal["story", "audio", "video", "edit", "done", "error"]
    status: Literal["queued", "running", "completed", "failed"]
    message: str
    percent: int = Field(ge=0, le=100)
    meta: Dict[str, Any] = Field(default_factory=dict)


class PipelineState(BaseModel):
    job_id: str
    user_prompt: str
    created_at: str
    updated_at: str
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    current_phase: Optional[str] = None
    story_spec_path: Optional[str] = None
    timing_manifest_path: Optional[str] = None
    final_video_path: Optional[str] = None
    progress: List[PipelineProgress] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class EditRequest(BaseModel):
    query: str = Field(min_length=3)


class EditIntent(BaseModel):
    intent: str
    target: Literal["audio", "video_frame", "video", "script"]
    confidence: float = Field(ge=0.0, le=1.0)
    params: Dict[str, Any] = Field(default_factory=dict)


class EditResult(BaseModel):
    applied: bool
    target: str
    details: str
    updated_state_path: Optional[str] = None
    rerender_required: bool = False
