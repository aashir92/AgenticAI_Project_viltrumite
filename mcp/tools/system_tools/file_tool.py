from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from mcp.base_tool import BaseTool


class FileTool(BaseTool):
    name = "file_tool"
    description = "Basic file operations."

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs["action"]
        path = Path(kwargs["path"])
        if action == "exists":
            return {"exists": path.exists()}
        if action == "read_text":
            return {"text": path.read_text(encoding="utf-8")}
        if action == "write_text":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(kwargs.get("text", ""), encoding="utf-8")
            return {"ok": True}
        raise ValueError(f"Unsupported action: {action}")
