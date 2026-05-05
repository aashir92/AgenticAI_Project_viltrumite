from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw
from scipy.io import wavfile

from mcp.tools.video_tools import ImageCompositorTool
from mcp.tools.vision_tools import HFImageGenTool, ImageBackgroundRemovalTool
from shared.constants import DEFAULT_VIDEO_FPS, DEFAULT_VIDEO_RESOLUTION
from shared.schemas import StorySpec, TimingManifest
from shared.utils import setup_logger


class VideoAgent:
    def __init__(self) -> None:
        self.logger = setup_logger("video-agent")
        self.image_tool = HFImageGenTool()
        self.bg_removal_tool = ImageBackgroundRemovalTool()
        self.compositor = ImageCompositorTool()

    def _mouth_open_ratio(self, audio_path: str, t: float) -> float:
        sample_rate, data = wavfile.read(audio_path)
        if data.ndim > 1:
            data = data.mean(axis=1)
        win_samples = int(0.06 * sample_rate)
        center = int(t * sample_rate)
        start = max(0, center - win_samples // 2)
        end = min(len(data), start + win_samples)
        chunk = data[start:end]
        if len(chunk) == 0:
            return 0.0
        loudness = float((abs(chunk).mean()) / 5000.0)
        return float(max(0.0, min(1.0, loudness)))

    def _animate_mouth(self, frame_path: Path, out_path: Path, openness: float) -> Path:
        img = Image.open(frame_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        w, h = img.size
        mouth_w = int(w * 0.08)
        mouth_h = max(2, int(h * 0.02 + h * 0.03 * openness))
        x = int(w * 0.28)
        y = int(h * 0.74)
        draw.ellipse((x, y, x + mouth_w, y + mouth_h), fill=(120, 20, 20, 220))
        img.save(out_path)
        return out_path

    def run(self, job_id: str, story_spec_data: Dict, timing_manifest_data: Dict, master_audio_path: str) -> Dict:
        story = StorySpec.model_validate(story_spec_data)
        timing = TimingManifest.model_validate(timing_manifest_data)
        root = Path("data/outputs") / job_id / "video"
        root.mkdir(parents=True, exist_ok=True)
        clips: List[ImageClip] = []

        for scene_idx, scene in enumerate(story.scenes):
            bg_path = root / f"{scene.scene_id}_bg.png"
            self.image_tool.run(prompt=scene.visual_description, kind="background", output_path=str(bg_path))

            char_layers = []
            for character in story.characters:
                c_raw = root / f"{scene.scene_id}_{character.name}_raw.png"
                c_cut = root / f"{scene.scene_id}_{character.name}.png"
                self.image_tool.run(
                    prompt=f"visual novel character portrait, {character.visual_traits}, speaking pose, transparent-ready",
                    kind="character",
                    output_path=str(c_raw),
                )
                self.bg_removal_tool.run(input_path=str(c_raw), output_path=str(c_cut))
                char_layers.append(
                    {
                        "path": str(c_cut),
                        "scale": 0.65,
                        "position": (120 + len(char_layers) * 580, 180),
                    }
                )

            composite_path = root / f"{scene.scene_id}_composite.png"
            self.compositor.run(background_path=str(bg_path), character_layers=char_layers, output_path=str(composite_path))

            scene_entries = [e for e in timing.entries if e.scene_id == scene.scene_id]
            scene_duration = max(scene.duration_seconds, 1)
            segment_clip = ImageClip(str(composite_path)).set_duration(scene_duration)
            segment_clip = segment_clip.resize(width=DEFAULT_VIDEO_RESOLUTION[0]).resize(
                lambda t: 1.0 + 0.03 * (t / scene_duration)
            )
            segment_clip = segment_clip.set_position(lambda t: (-20 * (t / scene_duration), -8 * (t / scene_duration)))

            animated_overlays = []
            for entry in scene_entries:
                scene_start_ms = scene_entries[0].start_ms if scene_entries else 0
                local_start = max(0.0, (entry.start_ms - scene_start_ms) / 1000.0)
                local_end = max(local_start, (entry.end_ms - scene_start_ms) / 1000.0)
                t_cursor = local_start
                while t_cursor < local_end:
                    openness = self._mouth_open_ratio(entry.audio_file, t_cursor - local_start)
                    mouth_frame = root / f"mouth_{scene.scene_id}_{int(t_cursor*100)}.png"
                    self._animate_mouth(composite_path, mouth_frame, openness)
                    overlay = ImageClip(str(mouth_frame)).set_duration(min(0.08, local_end - t_cursor)).set_start(t_cursor)
                    animated_overlays.append(overlay)
                    t_cursor += 0.08

            scene_video = CompositeVideoClip([segment_clip, *animated_overlays], size=DEFAULT_VIDEO_RESOLUTION).set_duration(
                scene_duration
            )
            clips.append(scene_video)
            self.logger.info("Scene %s prepared.", scene.scene_id)

        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.set_audio(AudioFileClip(master_audio_path))
        output_path = root / "final_output.mp4"
        final_video.write_videofile(str(output_path), fps=DEFAULT_VIDEO_FPS, codec="libx264", audio_codec="aac")
        return {"final_video_path": str(output_path)}
