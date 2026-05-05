from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image

from mcp.base_tool import BaseTool


class ImageCompositorTool(BaseTool):
    name = "image_compositor"
    description = "Composite character layers over a shared background."

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        background_path = Path(kwargs["background_path"])
        character_layers: List[Dict[str, Any]] = kwargs["character_layers"]
        output_path = Path(kwargs["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)

        bg = Image.open(background_path).convert("RGBA")
        canvas = bg.copy()
        for layer in character_layers:
            char_img = Image.open(layer["path"]).convert("RGBA")
            scale = float(layer.get("scale", 1.0))
            pos: Tuple[int, int] = tuple(layer.get("position", (0, 0)))
            new_size = (max(1, int(char_img.width * scale)), max(1, int(char_img.height * scale)))
            char_img = char_img.resize(new_size, Image.Resampling.LANCZOS)
            canvas.alpha_composite(char_img, dest=pos)

        canvas.save(output_path)
        return {"image_path": str(output_path)}
