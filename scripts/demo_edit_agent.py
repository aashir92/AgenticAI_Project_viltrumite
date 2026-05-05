"""
Edit Agent - Scripted Demo (Non-Interactive, Windows-Safe)
============================================================
Runs a scripted sequence of edit queries against a mock pipeline state
and prints the intent classification + execution results.

Usage:
    conda activate agenticai
    python scripts/demo_edit_agent.py

Uses the LIVE Groq LLM for classification - no mocks.
"""
from __future__ import annotations

import json
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 output on Windows so characters don't crash cp1252
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

from agents.edit_agent.agent import EditAgent, EditAgentState

DEMO_QUERIES = [
    "Change Alice's hair colour to bright red",
    "Make the background in scene 2 look like a rainy night city",
    "Make Sam's voice sound angry and intense",
    "Change the dialogue in scene 1 so Leo says 'The system is compromised'",
    "Make the speech rate slower",
    "Add dramatic orchestral background music at low volume",
    "Make scene 3 longer, about 20 seconds",
    "Add bold white subtitles at the bottom",
    "undo",
    "undo",
    "Regenerate the entire video with all changes applied",
]

BANNER = """
================================================================
     Edit Agent Demo  -  Agentic AI Video Pipeline
     Live Groq LLM Classification  |  Undo Stack Demo
================================================================
"""


def print_step(i: int, query: str) -> None:
    print(f"\n{'─'*64}")
    print(f"[Step {i:02d}]  Query: \"{query}\"")


def print_result(intent, result, state_depth: int) -> None:
    print(f"  Intent     :  {intent.intent}")
    print(f"  Target     :  {intent.target}")
    print(f"  Confidence :  {intent.confidence:.0%}")
    if intent.params:
        print(f"  Params     :  {json.dumps(intent.params)}")
    print(f"  Applied    :  {'YES' if result.applied else 'NO'}")
    print(f"  Re-render  :  {'YES' if result.rerender_required else 'No'}")
    print(f"  Details    :  {result.details}")
    print(f"  Undo Depth :  {state_depth} level(s)")


def main() -> None:
    print(BANNER)

    print(f"Initialising Edit Agent (Groq: {os.getenv('GROQ_MODEL', 'default')})...")
    try:
        agent = EditAgent()
        print("Agent ready!\n")
    except Exception as e:
        print(f"Failed to init agent: {e}")
        sys.exit(1)

    # Simulated initial pipeline state
    state = EditAgentState({
        "job_id": "demo_job_001",
        "character_overrides": {},
        "background_overrides": {},
        "audio_overrides": {},
        "script_overrides": {},
        "duration_overrides": {},
    })

    errors = 0
    for i, query in enumerate(DEMO_QUERIES, 1):
        print_step(i, query)
        try:
            intent = agent.classify(query)
            result = agent.handle(query, state)
            print_result(intent, result, len(state._undo_stack))
        except Exception as e:
            errors += 1
            print(f"  ERROR: {e}")

    # Final state snapshot
    print(f"\n{'='*64}")
    print("Final Pipeline State Snapshot:")
    exclude = {"job_id", "last_edit"}
    for k, v in state.state.items():
        if k not in exclude and v:
            print(f"  {k}: {json.dumps(v)}")

    print(f"\n{'─'*64}")
    total = len(DEMO_QUERIES)
    passed = total - errors
    print(f"Demo complete: {passed}/{total} steps succeeded.")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
