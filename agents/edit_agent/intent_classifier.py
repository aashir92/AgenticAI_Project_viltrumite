from __future__ import annotations

from mcp.tools.llm_tools import GroqJsonStructurerTool
from shared.schemas import EditIntent


class EditIntentClassifier:
    def __init__(self) -> None:
        self.tool = GroqJsonStructurerTool()

    def classify(self, query: str) -> EditIntent:
        prompt = f"""
        Classify this edit request into target one of: audio, video_frame, video, script.
        Query: "{query}"
        Return JSON with intent, target, confidence, params.
        """
        result = self.tool.run(prompt=prompt, schema_model=EditIntent, attempts=2)["json"]
        return EditIntent.model_validate(result)
