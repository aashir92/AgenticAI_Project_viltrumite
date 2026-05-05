"""
Edit Agent – Unit Tests
========================
Tests cover 10+ edit query types, intent classification accuracy,
undo stack correctness, and error handling.

Run with:
    pytest agents/edit_agent/tests/test_edit_agent.py -v
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from agents.edit_agent.agent import EditAgent, EditAgentState, ClassifiedIntent
from shared.schemas import EditIntent, EditResult


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_mock_intent(intent: str, target: str = "video_frame", confidence: float = 0.95, params: dict | None = None) -> ClassifiedIntent:
    """Create a mock ClassifiedIntent without calling the LLM."""
    return ClassifiedIntent(
        intent=intent,
        target=target,
        confidence=confidence,
        params=params or {},
    )


def make_agent_with_mock(intent: str, target: str = "video_frame", confidence: float = 0.95, params: dict | None = None) -> EditAgent:
    """Return an EditAgent whose LLM classifier is mocked to return the given intent."""
    agent = EditAgent.__new__(EditAgent)
    agent.logger = MagicMock()

    mock_classifier = MagicMock()
    mock_classifier.invoke.return_value = make_mock_intent(intent, target, confidence, params)
    agent._classifier = mock_classifier
    return agent


# ─────────────────────────────────────────────────────────────────────────────
# EditAgentState – unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEditAgentState:
    def test_initial_state_empty(self):
        s = EditAgentState()
        assert s.state == {}

    def test_initial_state_with_data(self):
        s = EditAgentState({"key": "value"})
        assert s.state["key"] == "value"

    def test_apply_updates_state(self):
        s = EditAgentState()
        s.apply({"foo": "bar"})
        assert s.state["foo"] == "bar"

    def test_apply_pushes_to_undo_stack(self):
        s = EditAgentState()
        s.apply({"foo": "bar"})
        assert s.can_undo()

    def test_undo_restores_previous_state(self):
        s = EditAgentState({"color": "red"})
        s.apply({"color": "blue"})
        assert s.state["color"] == "blue"
        success = s.undo()
        assert success is True
        assert s.state["color"] == "red"

    def test_undo_empty_stack_returns_false(self):
        s = EditAgentState()
        assert s.undo() is False

    def test_multiple_undo_levels(self):
        s = EditAgentState({"v": 0})
        s.apply({"v": 1})
        s.apply({"v": 2})
        s.apply({"v": 3})
        s.undo()
        assert s.state["v"] == 2
        s.undo()
        assert s.state["v"] == 1
        s.undo()
        assert s.state["v"] == 0

    def test_can_undo_false_initially(self):
        s = EditAgentState()
        assert s.can_undo() is False

    def test_state_deep_copied_on_apply(self):
        """Mutations to state after apply must not corrupt undo stack."""
        s = EditAgentState({"items": [1, 2, 3]})
        s.apply({"items": [1, 2, 3, 4]})
        s.state["items"].append(999)  # mutate current state
        s.undo()
        # undo stack must have the original [1,2,3], not mutated version
        assert 999 not in s.state.get("items", [])


# ─────────────────────────────────────────────────────────────────────────────
# EditAgent – Intent Classification Tests (10 query types)
# ─────────────────────────────────────────────────────────────────────────────

class TestEditAgentClassification:
    """
    Each test mocks the Groq LLM so we do NOT need live API credentials.
    We verify that handle() maps the classified intent to the correct
    EditResult fields (target, rerender_required, applied).
    """

    # 1. Character Visuals
    def test_character_visuals_query(self):
        agent = make_agent_with_mock(
            "character_visuals",
            params={"character_name": "Alice", "trait": "blonde hair"},
        )
        state = EditAgentState()
        result = agent.handle("Change Alice's hair to blonde", state)
        assert result.applied is True
        assert result.rerender_required is True
        assert "Alice" in result.details
        assert state.state["character_overrides"]["Alice"] == "blonde hair"

    # 2. Background Visuals
    def test_background_visuals_query(self):
        agent = make_agent_with_mock(
            "background_visuals",
            params={"scene_id": "scene2", "description": "darker rainy night"},
        )
        state = EditAgentState()
        result = agent.handle("Make the background in scene 2 darker and rainy", state)
        assert result.applied is True
        assert result.rerender_required is True
        assert "scene2" in result.details

    # 3. Undo
    def test_undo_query_with_history(self):
        agent = make_agent_with_mock("undo", target="system")
        state = EditAgentState({"color": "red"})
        state.apply({"color": "blue"})  # add something to undo stack
        result = agent.handle("undo", state)
        assert result.applied is True
        assert "Undo successful" in result.details
        assert state.state["color"] == "red"

    def test_undo_query_nothing_to_undo(self):
        agent = make_agent_with_mock("undo", target="system")
        state = EditAgentState()
        result = agent.handle("undo last change", state)
        assert result.applied is False
        assert "Nothing to undo" in result.details

    # 4. Audio Emotion
    def test_audio_emotion_query(self):
        agent = make_agent_with_mock(
            "audio_emotion",
            target="audio",
            params={"character_name": "Sam", "emotion": "angry"},
        )
        state = EditAgentState()
        result = agent.handle("Make Sam sound angry", state)
        assert result.applied is True
        assert result.rerender_required is False  # no video re-render needed
        assert state.state["audio_overrides"]["Sam"] == "angry"

    # 5. Script Dialogue
    def test_script_dialogue_query(self):
        agent = make_agent_with_mock(
            "script_dialogue",
            target="script",
            params={"scene_id": "scene1", "new_text": "Hello there!"},
        )
        state = EditAgentState()
        result = agent.handle("Change the dialogue in scene 1 to say 'Hello there!'", state)
        assert result.applied is True
        assert result.rerender_required is True
        assert state.state["script_overrides"]["scene1"] == "Hello there!"

    # 6. Regenerate
    def test_regenerate_query(self):
        agent = make_agent_with_mock("regenerate", target="video")
        state = EditAgentState()
        result = agent.handle("Regenerate the entire video", state)
        assert result.applied is True
        assert result.rerender_required is True
        assert state.state.get("force_regenerate") is True

    # 7. Speed (TTS rate)
    def test_speed_query(self):
        agent = make_agent_with_mock(
            "speed",
            target="audio",
            params={"rate": 140},
        )
        state = EditAgentState()
        result = agent.handle("Make the speech slower", state)
        assert result.applied is True
        assert state.state.get("tts_rate") == 140

    # 8. Scene Duration
    def test_scene_duration_query(self):
        agent = make_agent_with_mock(
            "scene_duration",
            target="video",
            params={"scene_id": "scene3", "duration_seconds": 15},
        )
        state = EditAgentState()
        result = agent.handle("Make scene 3 longer, about 15 seconds", state)
        assert result.applied is True
        assert result.rerender_required is True
        assert state.state["duration_overrides"]["scene3"] == 15

    # 9. Subtitle
    def test_subtitle_query(self):
        agent = make_agent_with_mock(
            "subtitle",
            target="video",
            params={"enabled": True, "style": "bold white"},
        )
        state = EditAgentState()
        result = agent.handle("Add bold white subtitles", state)
        assert result.applied is True
        assert "subtitle" in state.state

    # 10. Music
    def test_music_query(self):
        agent = make_agent_with_mock(
            "music",
            target="audio",
            params={"genre": "dramatic orchestral", "volume": 0.3},
        )
        state = EditAgentState()
        result = agent.handle("Add dramatic orchestral background music", state)
        assert result.applied is True
        assert "music" in state.state
        assert state.state["music"]["genre"] == "dramatic orchestral"

    # 11. Unknown intent
    def test_unknown_intent_query(self):
        agent = make_agent_with_mock("unknown", confidence=0.2)
        state = EditAgentState()
        result = agent.handle("Turn the video into a podcast somehow", state)
        # Should still apply without crashing
        assert result.applied is True

    # 12. Multiple edits + multi-level undo
    def test_multi_edit_and_undo_chain(self):
        state = EditAgentState()

        agent1 = make_agent_with_mock("character_visuals", params={"character_name": "Alice", "trait": "red hair"})
        agent1.handle("Make Alice red hair", state)

        agent2 = make_agent_with_mock("background_visuals", params={"scene_id": "scene1", "description": "sunset"})
        agent2.handle("Change scene 1 background to sunset", state)

        assert state.state["character_overrides"]["Alice"] == "red hair"
        assert state.state["background_overrides"]["scene1"] == "sunset"

        # Undo background
        undo_agent = make_agent_with_mock("undo", target="system")
        r1 = undo_agent.handle("undo", state)
        assert r1.applied is True
        assert "background_overrides" not in state.state or "scene1" not in state.state.get("background_overrides", {})

        # Undo character
        r2 = undo_agent.handle("undo", state)
        assert r2.applied is True

        # No more to undo
        r3 = undo_agent.handle("undo", state)
        assert r3.applied is False


# ─────────────────────────────────────────────────────────────────────────────
# EditAgent – classify() returns correct EditIntent schema
# ─────────────────────────────────────────────────────────────────────────────

class TestEditAgentClassifySchema:
    def test_classify_returns_edit_intent(self):
        agent = make_agent_with_mock("audio_emotion", target="audio", confidence=0.9)
        intent = agent.classify("Make Sam sound sad")
        assert isinstance(intent, EditIntent)
        assert intent.intent == "audio_emotion"
        assert intent.target == "audio"
        assert 0.0 <= intent.confidence <= 1.0

    def test_classify_maps_target_correctly(self):
        """character_visuals must map to video_frame target."""
        agent = make_agent_with_mock("character_visuals")
        intent = agent.classify("Change hair color")
        assert intent.target == "video_frame"

    def test_classify_undo_maps_to_system(self):
        agent = make_agent_with_mock("undo", target="system")
        intent = agent.classify("undo")
        assert intent.target == "system"


# ─────────────────────────────────────────────────────────────────────────────
# Phase-level Integration: Input → Output contract
# ─────────────────────────────────────────────────────────────────────────────

class TestPhaseLevelContracts:
    """Verify that each module respects its input/output contract."""

    def test_edit_agent_state_input_output(self):
        """apply() takes Dict, returns None; state is updated Dict."""
        s = EditAgentState({"x": 1})
        result = s.apply({"y": 2})
        assert result is None  # no return value
        assert s.state == {"x": 1, "y": 2}

    def test_handle_output_is_edit_result(self):
        agent = make_agent_with_mock("regenerate", target="video")
        result = agent.handle("Redo everything", EditAgentState())
        assert isinstance(result, EditResult)
        assert hasattr(result, "applied")
        assert hasattr(result, "target")
        assert hasattr(result, "details")
        assert hasattr(result, "rerender_required")

    def test_handle_with_none_params_does_not_crash(self):
        agent = make_agent_with_mock("script_dialogue", target="script", params={})
        state = EditAgentState()
        result = agent.handle("Change the script somehow", state)
        assert isinstance(result, EditResult)

    def test_undo_stack_isolation_between_states(self):
        """Two separate EditAgentState instances must not share undo stacks."""
        s1 = EditAgentState({"owner": "s1"})
        s2 = EditAgentState({"owner": "s2"})
        s1.apply({"extra": "only_in_s1"})
        assert not s2.can_undo()
