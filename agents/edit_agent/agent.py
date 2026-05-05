"""
Edit Intent Classification Agent
==================================
LangGraph/LangChain node that classifies a free-text edit request into a
structured EditIntent, then executes or undoes that intent.

Every successful edit is persisted as a versioned JSON snapshot under
  data/state_versions/{job_id}/v_N.json
so that history survives restarts and the Undo operation can load from disk.

Supported intent types
-----------------------
character_visuals   - change a character's appearance
background_visuals  - change a scene's background look
audio_emotion       - change how a character's voice sounds
script_dialogue     - change the spoken lines
regenerate          - re-run the full pipeline
undo                - revert the last edit
speed               - adjust playback/speech rate
scene_duration      - lengthen or shorten a scene
subtitle            - add/remove/change subtitles
music               - add/change background music
"""

from __future__ import annotations

import copy
import os
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from shared.schemas import EditIntent, EditResult
from shared.utils import setup_logger
from state_manager.state_manager import StateManager

logger = setup_logger("edit-agent")

# ---------------------------------------------------------------------------
# Pydantic model the LLM must return
# ---------------------------------------------------------------------------

SUPPORTED_INTENTS = [
    "character_visuals", "background_visuals", "audio_emotion",
    "script_dialogue", "regenerate", "undo", "speed",
    "scene_duration", "subtitle", "music", "unknown",
]


class ClassifiedIntent(BaseModel):
    """Structured output the LLM must produce."""
    intent: str = Field(
        description=(
            "One of: character_visuals, background_visuals, audio_emotion, "
            "script_dialogue, regenerate, undo, speed, scene_duration, "
            "subtitle, music, unknown"
        )
    )
    target: str = Field(
        description="Affected pipeline target: audio, video_frame, video, script, or system"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="0.0-1.0")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs extracted from the query",
    )


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an expert video-editing assistant for a visual-novel pipeline.
Your job is to classify a user's edit request into a structured JSON object with these fields:

intent   - MUST be one of: character_visuals, background_visuals, audio_emotion,
           script_dialogue, regenerate, undo, speed, scene_duration, subtitle, music, unknown
target   - MUST be one of: audio, video_frame, video, script, system
confidence - float 0.0-1.0
params   - JSON object with any relevant extracted values, e.g.:
           {"scene_id": "scene1", "character_name": "Alice", "trait": "blonde hair"}

Always respond ONLY with a valid JSON object matching the schema. No extra text.
"""


# ---------------------------------------------------------------------------
# EditAgentState  (in-memory undo stack + disk persistence via StateManager)
# ---------------------------------------------------------------------------

class EditAgentState:
    """
    Holds the mutable pipeline state and an undo history stack.
    When a job_id is present, every mutation is also persisted to
    data/state_versions/{job_id}/ via StateManager so history survives
    server restarts.
    """

    def __init__(self, initial_state: Optional[Dict] = None, job_id: Optional[str] = None) -> None:
        self._state: Dict = initial_state or {}
        self._undo_stack: List[Dict] = []
        self._job_id: Optional[str] = job_id or (initial_state or {}).get("job_id")
        self._sm: Optional[StateManager] = StateManager() if self._job_id else None

    @property
    def state(self) -> Dict:
        return self._state

    def apply(self, patch: Dict, note: str = "") -> None:
        """Save current state to undo stack, apply patch, persist snapshot to disk."""
        self._undo_stack.append(copy.deepcopy(self._state))
        self._state.update(patch)
        logger.info("Edit applied. Undo stack depth: %d", len(self._undo_stack))

        if self._sm and self._job_id:
            try:
                version = self._sm.snapshot(
                    job_id=self._job_id,
                    state=copy.deepcopy(self._state),
                    note=note or patch.get("last_edit", {}).get("intent", "edit"),
                )
                logger.info("State snapshot saved: v_%d (job=%s)", version, self._job_id)
            except Exception as exc:
                logger.warning("Could not persist state snapshot: %s", exc)

    def undo(self) -> bool:
        """Pop the last state. Returns True if successful. Persists the reverted state."""
        if not self._undo_stack:
            logger.warning("Nothing to undo.")
            return False
        self._state = self._undo_stack.pop()
        logger.info("Undo successful. Undo stack depth: %d", len(self._undo_stack))

        if self._sm and self._job_id:
            try:
                version = self._sm.snapshot(
                    job_id=self._job_id,
                    state=copy.deepcopy(self._state),
                    note="undo",
                )
                logger.info("Undo snapshot saved: v_%d (job=%s)", version, self._job_id)
            except Exception as exc:
                logger.warning("Could not persist undo snapshot: %s", exc)
        return True

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0


# ---------------------------------------------------------------------------
# EditAgent
# ---------------------------------------------------------------------------

class EditAgent:
    """
    Classifies a free-text edit request and applies / undoes it on
    an EditAgentState object.

    Usage
    -----
    agent = EditAgent()
    state = EditAgentState({"job_id": "abc123"})
    result = agent.handle("Make Alice's hair red", state)
    result = agent.handle("undo", state)
    """

    def __init__(self, model: Optional[str] = None) -> None:
        groq_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        llm = ChatGroq(
            model=groq_model,
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0,
        )
        self._classifier = llm.with_structured_output(ClassifiedIntent)
        self.logger = logger

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def classify(self, query: str) -> EditIntent:
        """Run the LLM intent classifier and return a validated EditIntent."""
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=query),
        ]
        classified: ClassifiedIntent = self._classifier.invoke(messages)
        intent_target_map = {
            "character_visuals": "video_frame",
            "background_visuals": "video_frame",
            "audio_emotion": "audio",
            "script_dialogue": "script",
            "regenerate": "video",
            "undo": "system",
            "speed": "audio",
            "scene_duration": "video",
            "subtitle": "video",
            "music": "audio",
            "unknown": "video",
        }
        target = intent_target_map.get(classified.intent, "video")
        return EditIntent(
            intent=classified.intent,
            target=target,
            confidence=classified.confidence,
            params=classified.params,
        )

    def handle(self, query: str, state: EditAgentState) -> EditResult:
        """
        Classify the query, execute or undo it on the given state, persist to disk.
        Returns an EditResult describing what happened.
        """
        edit_intent = self.classify(query)
        self.logger.info(
            "Intent classified: %s (target=%s, confidence=%.2f)",
            edit_intent.intent, edit_intent.target, edit_intent.confidence,
        )

        # ---- undo ------------------------------------------------------------
        if edit_intent.intent == "undo":
            success = state.undo()
            return EditResult(
                applied=success,
                target="system",
                details="Undo successful." if success else "Nothing to undo.",
                rerender_required=success,
            )

        # ---- apply edit -------------------------------------------------------
        patch: Dict[str, Any] = {
            "last_edit": {
                "query": query,
                "intent": edit_intent.intent,
                "params": edit_intent.params,
            }
        }
        rerender = False
        details = f"Edit intent '{edit_intent.intent}' recorded."

        if edit_intent.intent == "character_visuals":
            char  = edit_intent.params.get("character_name", "unknown")
            trait = edit_intent.params.get("trait", "unspecified change")
            patch["character_overrides"] = {**state.state.get("character_overrides", {}), char: trait}
            details  = f"Character '{char}' visual updated: {trait}. Re-render required."
            rerender = True

        elif edit_intent.intent == "background_visuals":
            scene = edit_intent.params.get("scene_id", "all")
            desc  = edit_intent.params.get("description", "updated look")
            patch["background_overrides"] = {**state.state.get("background_overrides", {}), scene: desc}
            details  = f"Background for scene '{scene}' updated: {desc}. Re-render required."
            rerender = True

        elif edit_intent.intent == "audio_emotion":
            char    = edit_intent.params.get("character_name", "unknown")
            emotion = edit_intent.params.get("emotion", "neutral")
            patch["audio_overrides"] = {**state.state.get("audio_overrides", {}), char: emotion}
            details = f"Audio emotion for '{char}' set to '{emotion}'."

        elif edit_intent.intent == "script_dialogue":
            scene    = edit_intent.params.get("scene_id", "all")
            new_text = edit_intent.params.get("new_text", "")
            patch["script_overrides"] = {**state.state.get("script_overrides", {}), scene: new_text}
            details  = f"Dialogue for scene '{scene}' updated. Full re-render required."
            rerender = True

        elif edit_intent.intent == "regenerate":
            patch["force_regenerate"] = True
            details  = "Full pipeline regeneration requested."
            rerender = True

        elif edit_intent.intent == "speed":
            rate = edit_intent.params.get("rate", 165)
            patch["tts_rate"] = rate
            details = f"TTS speech rate set to {rate} wpm."

        elif edit_intent.intent == "scene_duration":
            scene = edit_intent.params.get("scene_id", "all")
            secs  = edit_intent.params.get("duration_seconds", 10)
            patch["duration_overrides"] = {**state.state.get("duration_overrides", {}), scene: secs}
            details  = f"Scene '{scene}' duration set to {secs}s. Re-render required."
            rerender = True

        elif edit_intent.intent in ("subtitle", "music"):
            patch[edit_intent.intent] = edit_intent.params
            details = f"Setting '{edit_intent.intent}' updated with {edit_intent.params}."

        state.apply(patch, note=edit_intent.intent)
        return EditResult(
            applied=True,
            target=edit_intent.target,
            details=details,
            rerender_required=rerender,
        )
