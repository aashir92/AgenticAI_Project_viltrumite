from __future__ import annotations

from typing import Any, Dict

from langchain_groq import ChatGroq

from mcp.base_tool import BaseTool
from shared.utils import get_settings


class GroqTextGeneratorTool(BaseTool):
    name = "groq_text_generator"
    description = "Generate text responses with Groq."

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        prompt = kwargs.get("prompt", "")
        system = kwargs.get("system", "You are a precise assistant.")
        if not prompt:
            raise ValueError("prompt is required.")
        settings = get_settings()
        llm = ChatGroq(api_key=settings.groq_api_key, model=settings.groq_model, temperature=kwargs.get("temperature", 0.4))
        response = llm.invoke([("system", system), ("human", prompt)])
        return {"text": response.content}
