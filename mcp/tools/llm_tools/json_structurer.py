from __future__ import annotations

import json
from typing import Any, Dict, Type

from pydantic import BaseModel, ValidationError

from mcp.base_tool import BaseTool
from mcp.tools.llm_tools.text_generator import GroqTextGeneratorTool


class GroqJsonStructurerTool(BaseTool):
    name = "groq_json_structurer"
    description = "Generate and validate JSON with Groq."

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        prompt = kwargs["prompt"]
        schema_model: Type[BaseModel] = kwargs["schema_model"]
        attempts = kwargs.get("attempts", 3)
        generator = GroqTextGeneratorTool()
        error_context = ""

        for _ in range(attempts):
            final_prompt = (
                f"{prompt}\n\nReturn only valid JSON, no markdown.\n"
                f"Schema notes: {schema_model.model_json_schema()}\n{error_context}"
            )
            out = generator.run(prompt=final_prompt, system=kwargs.get("system", "You return strict JSON only."))["text"]
            try:
                payload = json.loads(out)
                parsed = schema_model.model_validate(payload)
                return {"json": parsed.model_dump()}
            except (json.JSONDecodeError, ValidationError) as exc:
                error_context = f"\nFix previous validation issue: {exc}"
        raise ValueError("Could not produce valid JSON after retries.")
