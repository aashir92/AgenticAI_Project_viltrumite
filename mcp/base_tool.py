from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = ""

    @abstractmethod
    def run(self, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError
