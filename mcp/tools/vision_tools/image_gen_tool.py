from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote

import requests
from PIL import Image

from mcp.base_tool import BaseTool


class HFImageGenTool(BaseTool):
    name = "hf_image_gen"
    description = "Generate images using free Pollinations API (formerly Hugging Face)."

    def _call_pollinations(self, prompt: str, kind: str) -> Image.Image:
        # Optimize prompt resolution based on kind
        width, height = (1280, 720) if kind == "background" else (768, 1024)
        
        # We append some style tags for better visual novel consistency
        style_suffix = ", high quality anime visual novel style, masterpiece"
        full_prompt = prompt + style_suffix
        encoded_prompt = quote(full_prompt)
        
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        
        # Add retries and longer timeout for free API stability under heavy load
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 120 seconds timeout to allow for queueing on their end
                response = requests.get(url, timeout=120)
                response.raise_for_status()
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)
        
        image = Image.open(io.BytesIO(response.content))
        return image.convert("RGBA")

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        prompt = kwargs["prompt"]
        kind = kwargs.get("kind", "background")
        output_path = Path(kwargs["output_path"])
        
        image = self._call_pollinations(prompt, kind)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return {"image_path": str(output_path)}
