from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from mcp.base_tool import BaseTool


class FFmpegTool(BaseTool):
    name = "ffmpeg_exec"
    description = "Run FFmpeg commands for media post-processing."

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        command = kwargs["command"]
        if isinstance(command, str):
            cmd = command.split()
        else:
            cmd = command
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        out = kwargs.get("output_path")
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
        return {"stdout": result.stdout, "stderr": result.stderr}
