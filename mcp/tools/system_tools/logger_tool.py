from __future__ import annotations

from typing import Any, Dict

from mcp.base_tool import BaseTool
from shared.utils import setup_logger


class LoggerTool(BaseTool):
    name = "logger_tool"
    description = "Write centralized log messages."

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        logger = setup_logger(kwargs.get("name", "agentic-system"))
        level = kwargs.get("level", "info").lower()
        message = kwargs.get("message", "")
        getattr(logger, level, logger.info)(message)
        return {"logged": True}
