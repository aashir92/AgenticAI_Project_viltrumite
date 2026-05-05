from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from scipy.io import wavfile

from mcp.base_tool import BaseTool


class AudioMergerTool(BaseTool):
    name = "audio_merger"
    description = "Merge multiple audio files into one track."

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        input_files: List[str] = kwargs["input_files"]
        output_path = Path(kwargs["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)

        chunks = []
        sample_rate = None
        for file in input_files:
            sr, data = wavfile.read(file)
            if sample_rate is None:
                sample_rate = sr
            if sr != sample_rate:
                raise ValueError(f"Inconsistent sample rate: {file} has {sr}, expected {sample_rate}")
            if data.ndim > 1:
                data = data.mean(axis=1).astype(data.dtype)
            chunks.append(data.astype(np.int16))

        if not chunks:
            raise ValueError("No input files provided for merge.")

        merged = np.concatenate(chunks, axis=0)
        wavfile.write(str(output_path), sample_rate, merged)
        duration_ms = int((len(merged) / sample_rate) * 1000)
        return {"audio_path": str(output_path), "duration_ms": duration_ms}
