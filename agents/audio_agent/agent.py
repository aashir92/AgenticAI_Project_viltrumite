from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from scipy.io import wavfile

from mcp.tools.audio_tools import AudioMergerTool, CoquiTTSTool
from shared.schemas import StorySpec, TimingEntry, TimingManifest
from shared.utils import setup_logger, write_json


class AudioAgent:
    def __init__(self) -> None:
        self.logger = setup_logger("audio-agent")
        self.tts_tool = CoquiTTSTool()
        self.merger_tool = AudioMergerTool()

    def run(self, job_id: str, story_spec_data: Dict) -> Dict:
        story = StorySpec.model_validate(story_spec_data)
        out_dir = Path("data/outputs") / job_id / "audio"
        out_dir.mkdir(parents=True, exist_ok=True)

        entries: List[TimingEntry] = []
        master_files: List[str] = []
        current_ms = 0

        for scene in story.scenes:
            for idx, line in enumerate(scene.dialogue):
                file_path = out_dir / f"{scene.scene_id}_{idx:02d}_{line.speaker}.wav"
                self.tts_tool.run(text=line.text, output_path=str(file_path))
                sr, data = wavfile.read(str(file_path))
                duration_ms = int((len(data) / sr) * 1000)
                start_ms = current_ms
                end_ms = current_ms + duration_ms
                entries.append(
                    TimingEntry(
                        scene_id=scene.scene_id,
                        speaker=line.speaker,
                        text=line.text,
                        audio_file=str(file_path),
                        start_ms=start_ms,
                        end_ms=end_ms,
                    )
                )
                current_ms = end_ms
                master_files.append(str(file_path))

        master_path = out_dir / "master_dialogue.wav"
        self.merger_tool.run(input_files=master_files, output_path=str(master_path))

        manifest = TimingManifest(entries=entries, total_duration_ms=current_ms)
        manifest_path = out_dir / "timing_manifest.json"
        write_json(manifest_path, manifest.model_dump())
        self.logger.info("Timing manifest generated at %s", manifest_path)
        return {
            "timing_manifest": manifest.model_dump(),
            "timing_manifest_path": str(manifest_path),
            "master_audio_path": str(master_path),
        }
