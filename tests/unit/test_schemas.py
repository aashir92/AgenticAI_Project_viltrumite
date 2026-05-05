"""
Unit Tests – Shared Schemas (Pydantic models)
================================================
Tests that all Pydantic models in shared/schemas validate correctly,
raise the right errors on bad input, and produce expected output shapes.

Run:
    conda activate agenticai
    python -m pytest tests/unit/test_schemas.py -v
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from shared.schemas import (
    CharacterSpec,
    DialogueLine,
    EditIntent,
    EditRequest,
    EditResult,
    PipelineProgress,
    SceneSpec,
    StorySpec,
    TimingEntry,
    TimingManifest,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_valid_story() -> dict:
    return {
        "story": "Two AIs solve a crisis",
        "theme": "cyberpunk",
        "characters": [
            {"name": "Astra", "voice_personality": "calm", "visual_traits": "silver hair"},
            {"name": "Leo",   "voice_personality": "sharp", "visual_traits": "dark hoodie"},
        ],
        "scenes": [
            {
                "scene_id": "scene1",
                "title": "Boot-up",
                "visual_description": "neon server room",
                "duration_seconds": 18,
                "dialogue": [
                    {"speaker": "Astra", "text": "Systems online.", "emotion": "calm"},
                    {"speaker": "Leo",   "text": "Run diagnostics.", "emotion": "focused"},
                ],
            },
            {
                "scene_id": "scene2",
                "title": "Breach",
                "visual_description": "dark corridor",
                "duration_seconds": 18,
                "dialogue": [
                    {"speaker": "Leo",   "text": "Intrusion detected.", "emotion": "alarmed"},
                    {"speaker": "Astra", "text": "Initiating lockdown.", "emotion": "urgent"},
                ],
            },
            {
                "scene_id": "scene3",
                "title": "Resolution",
                "visual_description": "control room at dawn",
                "duration_seconds": 18,
                "dialogue": [
                    {"speaker": "Astra", "text": "Threat neutralised.", "emotion": "relieved"},
                    {"speaker": "Leo",   "text": "Good work.", "emotion": "satisfied"},
                ],
            },
        ],
    }


# ══════════════════════════════════════════════════════════════════
# CharacterSpec
# ══════════════════════════════════════════════════════════════════
class TestCharacterSpec:
    def test_valid_character(self):
        c = CharacterSpec(name="Astra", voice_personality="calm", visual_traits="silver hair")
        assert c.name == "Astra"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            CharacterSpec(voice_personality="calm", visual_traits="silver")  # type: ignore


# ══════════════════════════════════════════════════════════════════
# DialogueLine
# ══════════════════════════════════════════════════════════════════
class TestDialogueLine:
    def test_default_emotion(self):
        line = DialogueLine(speaker="Leo", text="Hello")
        assert line.emotion == "neutral"

    def test_custom_emotion(self):
        line = DialogueLine(speaker="Leo", text="Hello", emotion="angry")
        assert line.emotion == "angry"


# ══════════════════════════════════════════════════════════════════
# SceneSpec
# ══════════════════════════════════════════════════════════════════
class TestSceneSpec:
    def test_valid_scene(self):
        s = SceneSpec(
            scene_id="scene1",
            title="Start",
            visual_description="a room",
            duration_seconds=10,
            dialogue=[DialogueLine(speaker="A", text="Hi")],
        )
        assert s.duration_seconds == 10

    def test_duration_too_short_raises(self):
        with pytest.raises(ValidationError):
            SceneSpec(
                scene_id="s", title="t", visual_description="d",
                duration_seconds=2,       # below minimum of 6
                dialogue=[],
            )

    def test_duration_too_long_raises(self):
        with pytest.raises(ValidationError):
            SceneSpec(
                scene_id="s", title="t", visual_description="d",
                duration_seconds=30,      # above maximum of 25
                dialogue=[],
            )


# ══════════════════════════════════════════════════════════════════
# StorySpec
# ══════════════════════════════════════════════════════════════════
class TestStorySpec:
    def test_valid_story_parses(self):
        story = StorySpec.model_validate(_make_valid_story())
        assert len(story.characters) == 2
        assert len(story.scenes) == 3

    def test_unknown_speaker_raises(self):
        data = _make_valid_story()
        data["scenes"][0]["dialogue"][0]["speaker"] = "Ghost"
        with pytest.raises(ValidationError, match="Unknown speaker"):
            StorySpec.model_validate(data)

    def test_total_duration_too_short_raises(self):
        data = _make_valid_story()
        for sc in data["scenes"]:
            sc["duration_seconds"] = 6   # 3 * 6 = 18 < 50
        with pytest.raises(ValidationError, match="approximately 1 minute"):
            StorySpec.model_validate(data)

    def test_too_few_characters_raises(self):
        data = _make_valid_story()
        data["characters"] = [data["characters"][0]]  # only 1 character
        with pytest.raises(ValidationError):
            StorySpec.model_validate(data)

    def test_too_many_characters_raises(self):
        data = _make_valid_story()
        data["characters"].append(
            {"name": "Zed", "voice_personality": "deep", "visual_traits": "tall"}
        )
        with pytest.raises(ValidationError):
            StorySpec.model_validate(data)


# ══════════════════════════════════════════════════════════════════
# TimingEntry
# ══════════════════════════════════════════════════════════════════
class TestTimingEntry:
    def test_valid_entry(self):
        e = TimingEntry(
            scene_id="scene1", speaker="Astra", text="Hi",
            audio_file="path/to/file.wav",
            start_ms=0, end_ms=1500,
        )
        assert e.end_ms > e.start_ms

    def test_end_before_start_raises(self):
        with pytest.raises(ValidationError, match="end_ms must be greater"):
            TimingEntry(
                scene_id="s", speaker="A", text="T",
                audio_file="f.wav",
                start_ms=2000, end_ms=1000,
            )

    def test_end_equal_start_raises(self):
        with pytest.raises(ValidationError):
            TimingEntry(
                scene_id="s", speaker="A", text="T",
                audio_file="f.wav",
                start_ms=1000, end_ms=1000,
            )


# ══════════════════════════════════════════════════════════════════
# TimingManifest
# ══════════════════════════════════════════════════════════════════
class TestTimingManifest:
    def test_valid_manifest(self):
        m = TimingManifest(
            entries=[
                TimingEntry(scene_id="s1", speaker="A", text="T",
                            audio_file="f.wav", start_ms=0, end_ms=1000)
            ],
            total_duration_ms=3000,
        )
        assert m.total_duration_ms == 3000

    def test_zero_duration_raises(self):
        with pytest.raises(ValidationError):
            TimingManifest(entries=[], total_duration_ms=0)


# ══════════════════════════════════════════════════════════════════
# PipelineProgress
# ══════════════════════════════════════════════════════════════════
class TestPipelineProgress:
    def test_valid_phases(self):
        for phase in ("story", "audio", "video", "edit", "done", "error"):
            p = PipelineProgress(phase=phase, status="running", message="ok", percent=50)
            assert p.phase == phase

    def test_invalid_phase_raises(self):
        with pytest.raises(ValidationError):
            PipelineProgress(phase="unknown", status="running", message="x", percent=0)

    def test_percent_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            PipelineProgress(phase="done", status="completed", message="x", percent=101)


# ══════════════════════════════════════════════════════════════════
# EditRequest
# ══════════════════════════════════════════════════════════════════
class TestEditRequest:
    def test_valid_request(self):
        r = EditRequest(query="make background darker")
        assert r.query == "make background darker"

    def test_query_too_short_raises(self):
        with pytest.raises(ValidationError):
            EditRequest(query="ab")   # min_length=3, "ab" has 2 chars


# ══════════════════════════════════════════════════════════════════
# EditIntent
# ══════════════════════════════════════════════════════════════════
class TestEditIntent:
    def test_valid_targets(self):
        for tgt in ("audio", "video_frame", "video", "script", "system"):
            i = EditIntent(intent="test", target=tgt, confidence=0.9)
            assert i.target == tgt

    def test_invalid_target_raises(self):
        with pytest.raises(ValidationError):
            EditIntent(intent="test", target="unknown", confidence=0.9)

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            EditIntent(intent="test", target="audio", confidence=1.5)

    def test_params_default_empty_dict(self):
        i = EditIntent(intent="test", target="video", confidence=0.5)
        assert i.params == {}


# ══════════════════════════════════════════════════════════════════
# EditResult
# ══════════════════════════════════════════════════════════════════
class TestEditResult:
    def test_default_values(self):
        r = EditResult(applied=True, target="audio", details="done")
        assert r.rerender_required is False
        assert r.updated_state_path is None

    def test_rerender_flag(self):
        r = EditResult(applied=True, target="video", details="ok", rerender_required=True)
        assert r.rerender_required is True
