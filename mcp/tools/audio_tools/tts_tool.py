from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pyttsx3

from mcp.base_tool import BaseTool
from shared.utils import setup_logger


class CoquiTTSTool(BaseTool):
    name = "coqui_tts"
    description = "Generate speech audio with local TTS."
    _engine: pyttsx3.Engine | None = None

    def __init__(self) -> None:
        self.logger = setup_logger("tts-tool")

    def _model(self) -> pyttsx3.Engine:
        if self._engine is None:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 170)
        return self._engine

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        text = kwargs["text"]
        output_path = Path(kwargs["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tts = self._model()

        # Try to map voice by speaker name for consistency.
        speaker = str(kwargs.get("speaker", "")).lower().strip()
        if speaker:
            voices = tts.getProperty("voices")
            matched = next((v for v in voices if speaker in (v.name or "").lower()), None)
            if matched:
                tts.setProperty("voice", matched.id)
        tts.save_to_file(text, str(output_path))
        tts.runAndWait()
        self.logger.info("Generated TTS line at %s", output_path)
        return {"audio_path": str(output_path)}
