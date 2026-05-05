from __future__ import annotations

from typing import Dict, Type

from mcp.base_tool import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Type[BaseTool]] = {}

    def register(self, tool_cls: Type[BaseTool]) -> None:
        self._tools[tool_cls.name] = tool_cls

    def build(self, tool_name: str) -> BaseTool:
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' not registered.")
        return self._tools[tool_name]()

    def list_tools(self) -> Dict[str, str]:
        return {name: cls.description for name, cls in self._tools.items()}
