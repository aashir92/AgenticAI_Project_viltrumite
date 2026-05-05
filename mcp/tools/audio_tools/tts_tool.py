from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pyttsx3

from mcp.base_tool import BaseTool
from shared.utils import setup_logger


class CoquiTTSTool(BaseTool):
    name = "coqui_tts"
    description = "Generate speech audio with local TTS, with gender-aware voice selection."

    def __init__(self) -> None:
        self.logger = setup_logger("tts-tool")

    def _get_female_voice_id(self) -> str | None:
        """Return the COM voice token for a female SAPI5 voice, or None."""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            engine.stop()
            for v in voices:
                name_lower = v.name.lower()
                # Windows SAPI5: Zira is female, David is male
                if any(kw in name_lower for kw in ("zira", "female", "woman", "helen", "hazel")):
                    return v.id
            # Fallback: voice index 1 is commonly female on Windows
            if len(voices) > 1:
                return voices[1].id
        except Exception:
            pass
        return None

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        text = kwargs["text"]
        output_path = Path(kwargs["output_path"])
        gender = kwargs.get("gender", "male").lower()  # "male" or "female"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        voice_id_line = ""
        if gender == "female":
            female_id = self._get_female_voice_id()
            if female_id:
                # Escape backslashes for embedding in the script string
                safe_id = female_id.replace("\\", "\\\\")
                voice_id_line = f"engine.setProperty('voice', r'{safe_id}')"

        # Run pyttsx3 in a subprocess to avoid SAPI5 COM deadlocks in thread pools
        script = f"""
import pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 165)
{voice_id_line}
engine.save_to_file({repr(text)}, {repr(str(output_path))})
engine.runAndWait()
"""
        subprocess.run([sys.executable, "-c", script], check=True)
        self.logger.info("Generated TTS line at %s (gender=%s)", output_path, gender)
        return {"audio_path": str(output_path)}
