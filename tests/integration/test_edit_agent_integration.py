"""
Integration Tests – Edit Agent  (live Groq LLM)
================================================
Verifies the full handle() pipeline:
  user query -> LLM classification -> state mutation -> EditResult

These tests hit the real Groq API and require GROQ_API_KEY in .env.
Each test uses an isolated EditAgentState so there is no cross-test leakage.

Run:
    conda activate agenticai
    python -m pytest tests/integration/test_edit_agent_integration.py -v
"""
from __future__ import annotations

import os
import pytest
from dotenv import load_dotenv

load_dotenv()

# Skip all tests in this module if no API key is configured
pytestmark = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set – skipping live integration tests",
)

from agents.edit_agent.agent import EditAgent, EditAgentState
from shared.schemas import EditIntent, EditResult


# ── Shared agent (one initialisation for the whole module) ────────────────────

@pytest.fixture(scope="module")
def agent() -> EditAgent:
    return EditAgent()


def fresh_state() -> EditAgentState:
    return EditAgentState({
        "job_id": "integ_test",
        "character_overrides": {},
        "background_overrides": {},
        "audio_overrides": {},
        "script_overrides": {},
        "duration_overrides": {},
    })


# ══════════════════════════════════════════════════════════════════
# 1. Character visual edit
# ══════════════════════════════════════════════════════════════════
class TestCharacterVisualEdit:
    def test_hair_colour_intent(self, agent):
        state = fresh_state()
        result = agent.handle("Change Alice's hair to silver", state)
        assert isinstance(result, EditResult)
        assert result.applied is True
        assert result.rerender_required is True

    def test_hair_colour_updates_state(self, agent):
        state = fresh_state()
        agent.handle("Give Bob red eyes", state)
        # Some character key should appear in character_overrides
        assert len(state.state.get("character_overrides", {})) > 0

    def test_classify_returns_edit_intent(self, agent):
        intent = agent.classify("Change Alice's hair to silver")
        assert isinstance(intent, EditIntent)
        assert intent.target == "video_frame"
        assert intent.confidence > 0.5


# ══════════════════════════════════════════════════════════════════
# 2. Background visual edit
# ══════════════════════════════════════════════════════════════════
class TestBackgroundVisualEdit:
    def test_background_intent_applies(self, agent):
        state = fresh_state()
        result = agent.handle("Make scene 1 background look like a dark forest", state)
        assert result.applied is True
        assert "background" in result.details.lower() or result.rerender_required

    def test_background_overrides_stored(self, agent):
        state = fresh_state()
        agent.handle("Change scene 2 background to a snow-covered mountain", state)
        assert len(state.state.get("background_overrides", {})) > 0


# ══════════════════════════════════════════════════════════════════
# 3. Audio / TTS edit
# ══════════════════════════════════════════════════════════════════
class TestAudioEdit:
    def test_emotion_change_applies(self, agent):
        state = fresh_state()
        result = agent.handle("Make Aria's voice sound sad", state)
        assert result.applied is True
        assert result.target == "audio"

    def test_speech_speed_slower(self, agent):
        state = fresh_state()
        result = agent.handle("Make the speech slower", state)
        assert result.applied is True
        # tts_rate should be set lower
        assert state.state.get("tts_rate", 200) < 200

    def test_music_setting_stored(self, agent):
        state = fresh_state()
        agent.handle("Add soft piano background music", state)
        assert "music" in state.state


# ══════════════════════════════════════════════════════════════════
# 4. Script / dialogue edit
# ══════════════════════════════════════════════════════════════════
class TestScriptEdit:
    def test_dialogue_change_applies(self, agent):
        state = fresh_state()
        result = agent.handle(
            "Change the dialogue in scene 1 so Astra says 'Reboot complete'",
            state,
        )
        assert result.applied is True
        assert result.rerender_required is True

    def test_script_override_stored(self, agent):
        state = fresh_state()
        agent.handle("In scene 2, make Leo say 'Alert dismissed'", state)
        assert len(state.state.get("script_overrides", {})) > 0


# ══════════════════════════════════════════════════════════════════
# 5. Scene duration edit
# ══════════════════════════════════════════════════════════════════
class TestSceneDurationEdit:
    def test_duration_change_applies(self, agent):
        state = fresh_state()
        result = agent.handle("Make scene 2 last 15 seconds", state)
        assert result.applied is True

    def test_duration_stored(self, agent):
        state = fresh_state()
        agent.handle("Extend scene 3 to 20 seconds", state)
        assert len(state.state.get("duration_overrides", {})) > 0


# ══════════════════════════════════════════════════════════════════
# 6. Subtitle & misc settings
# ══════════════════════════════════════════════════════════════════
class TestMiscEdits:
    def test_subtitle_applies(self, agent):
        state = fresh_state()
        result = agent.handle("Add yellow subtitles at the bottom of the screen", state)
        assert result.applied is True

    def test_regenerate_intent(self, agent):
        state = fresh_state()
        result = agent.handle("Regenerate the full video now", state)
        assert result.applied is True
        assert result.rerender_required is True
        assert state.state.get("force_regenerate") is True


# ══════════════════════════════════════════════════════════════════
# 7. Undo  –  multi-level
# ══════════════════════════════════════════════════════════════════
class TestUndoIntegration:
    def test_single_undo_reverts_last_edit(self, agent):
        state = fresh_state()
        agent.handle("Change Alice's hair to green", state)
        agent.handle("Make scene 1 darker", state)
        depth_before = len(state._undo_stack)

        result = agent.handle("undo", state)

        assert result.applied is True
        assert len(state._undo_stack) == depth_before - 1

    def test_double_undo(self, agent):
        state = fresh_state()
        agent.handle("Make speech slower", state)
        agent.handle("Add subtitles", state)
        start_depth = len(state._undo_stack)

        agent.handle("undo", state)
        agent.handle("undo", state)

        assert len(state._undo_stack) == start_depth - 2

    def test_undo_on_empty_stack_is_graceful(self, agent):
        state = fresh_state()  # no prior edits
        result = agent.handle("undo", state)
        # Should not crash – just report nothing to undo
        assert result.applied is False or "nothing" in result.details.lower() or "no" in result.details.lower()

    def test_undo_restores_character_override(self, agent):
        state = fresh_state()
        agent.handle("Change Bob's hair to purple", state)
        depth_after_edit = len(state._undo_stack)

        result = agent.handle("undo", state)

        # Undo must succeed and reduce the stack
        assert result.applied is True
        assert len(state._undo_stack) == depth_after_edit - 1


# ══════════════════════════════════════════════════════════════════
# 8. Full edit → undo chain (end-to-end scenario)
# ══════════════════════════════════════════════════════════════════
class TestEndToEndChain:
    def test_five_edits_then_two_undos(self, agent):
        state = fresh_state()
        queries = [
            "Change Alice's hair to silver",
            "Make scene 2 background a sunset beach",
            "Make voices slower",
            "Add subtitles in white",
            "Make scene 3 longer, 18 seconds",
        ]
        for q in queries:
            agent.handle(q, state)

        depth_after_edits = len(state._undo_stack)
        agent.handle("undo", state)
        agent.handle("undo", state)

        assert len(state._undo_stack) == depth_after_edits - 2

    def test_all_edit_results_are_edit_result_instances(self, agent):
        state = fresh_state()
        results = [
            agent.handle("Change Bob's jacket to red", state),
            agent.handle("Set scene 1 background to cyberpunk alley", state),
            agent.handle("Make Leo's voice calm", state),
            agent.handle("undo", state),
        ]
        for r in results:
            assert isinstance(r, EditResult)

    def test_state_isolation_between_fresh_states(self, agent):
        state_a = fresh_state()
        state_b = fresh_state()

        agent.handle("Make Alice's hair blue", state_a)
        # state_b must NOT be affected
        assert state_b.state.get("character_overrides") == {}
