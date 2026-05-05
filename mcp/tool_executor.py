from __future__ import annotations

from typing import Any, Dict

from mcp.tool_registry import ToolRegistry


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        tool = self.registry.build(tool_name)
        return tool.run(**kwargs)
