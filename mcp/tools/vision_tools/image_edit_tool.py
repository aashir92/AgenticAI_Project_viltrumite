from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from PIL import Image
from rembg import remove

from mcp.base_tool import BaseTool


class ImageBackgroundRemovalTool(BaseTool):
    name = "image_bg_removal"
    description = "Remove background from character images."

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        input_path = Path(kwargs["input_path"])
        output_path = Path(kwargs["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        src = input_path.read_bytes()
        out = remove(src)
        output_path.write_bytes(out)
        Image.open(output_path).convert("RGBA").save(output_path)
        return {"image_path": str(output_path)}
