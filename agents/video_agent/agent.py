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

    def _get_audio_data(self, audio_path: str):
        sample_rate, data = wavfile.read(audio_path)
        if data.ndim > 1:
            data = data.mean(axis=1)
        return sample_rate, data

    def _mouth_open_ratio(self, data, sample_rate: int, t: float) -> float:
        win_samples = int(0.06 * sample_rate)
        center = int(t * sample_rate)
        start = max(0, center - win_samples // 2)
        end = min(len(data), start + win_samples)
        chunk = data[start:end]
        if len(chunk) == 0:
            return 0.0
        loudness = float((abs(chunk).mean()) / 5000.0)
        return float(max(0.0, min(1.0, loudness)))

    def _create_mouth_overlay(self, w: int, h: int, out_path: Path) -> Path:
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        mouth_w = int(w * 0.08)
        mouth_h = int(h * 0.04)
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
        
        # Generate Characters ONCE for the whole video
        self.logger.info("Generating characters...")
        char_layers = []
        for character in story.characters:
            c_raw = root / f"char_{character.name}_raw.png"
            c_cut = root / f"char_{character.name}.png"
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

        # Create one reusable mouth overlay
        mouth_path = root / "mouth_overlay.png"
        self._create_mouth_overlay(DEFAULT_VIDEO_RESOLUTION[0], DEFAULT_VIDEO_RESOLUTION[1], mouth_path)

        for scene_idx, scene in enumerate(story.scenes):
            bg_path = root / f"{scene.scene_id}_bg.png"
            bg_prompt = scene.visual_description + ", empty background, no people, no characters, scenic environment"
            self.image_tool.run(prompt=bg_prompt, kind="background", output_path=str(bg_path))

            composite_path = root / f"{scene.scene_id}_composite.png"
            self.compositor.run(background_path=str(bg_path), character_layers=char_layers, output_path=str(composite_path))

            scene_entries = [e for e in timing.entries if e.scene_id == scene.scene_id]
            scene_duration = max(scene.duration_seconds, 1)
            
            unzoomed_base = ImageClip(str(composite_path)).set_duration(scene_duration)
            animated_overlays = []
            
            for entry in scene_entries:
                scene_start_ms = scene_entries[0].start_ms if scene_entries else 0
                local_start = max(0.0, (entry.start_ms - scene_start_ms) / 1000.0)
                local_end = max(local_start, (entry.end_ms - scene_start_ms) / 1000.0)
                
                # Preload audio data
                sample_rate, data = self._get_audio_data(entry.audio_file)
                
                t_cursor = local_start
                while t_cursor < local_end:
                    openness = self._mouth_open_ratio(data, sample_rate, t_cursor - local_start)
                    dur = min(0.1, local_end - t_cursor)
                    if openness > 0.1:
                        overlay = ImageClip(str(mouth_path)).set_duration(dur).set_start(t_cursor)
                        animated_overlays.append(overlay)
                    t_cursor += 0.1

            unzoomed_scene = CompositeVideoClip([unzoomed_base, *animated_overlays], size=DEFAULT_VIDEO_RESOLUTION).set_duration(scene_duration)
            
            # Apply camera pan/zoom to the composited scene so the mouth doesn't float away
            scene_video = unzoomed_scene.resize(width=DEFAULT_VIDEO_RESOLUTION[0]).resize(
                lambda t: 1.0 + 0.03 * (t / scene_duration)
            ).set_position(lambda t: (-20 * (t / scene_duration), -8 * (t / scene_duration)))
            
            clips.append(scene_video)
            self.logger.info("Scene %s prepared.", scene.scene_id)

        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.set_audio(AudioFileClip(master_audio_path))
        output_path = root / "final_output.mp4"
        final_video.write_videofile(str(output_path), fps=DEFAULT_VIDEO_FPS, codec="libx264", audio_codec="aac")
        return {"final_video_path": str(output_path)}
