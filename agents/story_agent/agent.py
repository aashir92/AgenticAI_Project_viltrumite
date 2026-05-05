from __future__ import annotations

from pathlib import Path
from typing import Dict

from mcp.tools.llm_tools import GroqJsonStructurerTool
from shared.schemas import StorySpec
from shared.utils import setup_logger, write_json

from .planner import build_story_prompt


class StoryAgent:
    def __init__(self) -> None:
        self.logger = setup_logger("story-agent")
        self.generator = GroqJsonStructurerTool()

    def run(self, job_id: str, user_prompt: str) -> Dict:
        self.logger.info("Generating story for job %s", job_id)
        prompt = build_story_prompt(user_prompt)
        data = self.generator.run(prompt=prompt, schema_model=StorySpec, attempts=3)["json"]
        story_spec = StorySpec.model_validate(data)

        out_dir = Path("data/outputs") / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "story_spec.json"
        write_json(out_path, story_spec.model_dump())
        self.logger.info("Story written: %s", out_path)
        return {"story_spec": story_spec.model_dump(), "story_spec_path": str(out_path)}
