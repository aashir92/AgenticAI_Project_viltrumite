from __future__ import annotations

from shared.schemas import EditResult
from state_manager.state_manager import StateManager

from .executor import EditExecutor
from .intent_classifier import EditIntentClassifier
from .planner import build_edit_plan


class EditAgent:
    def __init__(self) -> None:
        self.classifier = EditIntentClassifier()
        self.executor = EditExecutor()
        self.state_manager = StateManager()

    def apply(self, job_id: str, query: str) -> dict:
        intent = self.classifier.classify(query)
        plan = build_edit_plan(intent)
        new_state = self.executor.execute(job_id=job_id, plan=plan)
        version = self.state_manager.snapshot(job_id=job_id, state=new_state, note=f"edit: {query}")
        result = EditResult(
            applied=True,
            target=intent.target,
            details=f"Applied edit intent '{intent.intent}'",
            updated_state_path=f"data/state_versions/{job_id}/v_{version}.json",
            rerender_required=plan["rerender_required"],
        )
        return {"intent": intent.model_dump(), "plan": plan, "result": result.model_dump()}

    def undo(self, job_id: str) -> dict:
        restored = self.state_manager.undo(job_id)
        return {"restored_state": restored, "message": "Reverted to previous state snapshot."}
