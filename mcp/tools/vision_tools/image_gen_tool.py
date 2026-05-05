from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Dict

import requests
from PIL import Image

from mcp.base_tool import BaseTool
from shared.utils import get_settings


class HFImageGenTool(BaseTool):
    name = "hf_image_gen"
    description = "Generate images using Hugging Face Inference API."

    def _call_hf(self, model: str, prompt: str) -> Image.Image:
        settings = get_settings()
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        res = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=180)
        res.raise_for_status()
        return Image.open(BytesIO(res.content)).convert("RGBA")

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        prompt = kwargs["prompt"]
        kind = kwargs.get("kind", "background")
        output_path = Path(kwargs["output_path"])
        settings = get_settings()
        model = settings.hf_background_model if kind == "background" else settings.hf_character_model
        image = self._call_hf(model, prompt)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return {"image_path": str(output_path)}
