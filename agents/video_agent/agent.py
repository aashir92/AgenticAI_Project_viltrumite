from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    VideoClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageEnhance
from scipy.io import wavfile

from mcp.tools.vision_tools import HFImageGenTool, ImageBackgroundRemovalTool
from shared.constants import DEFAULT_VIDEO_FPS, DEFAULT_VIDEO_RESOLUTION
from shared.schemas import StorySpec, TimingManifest
from shared.utils import setup_logger

W, H = DEFAULT_VIDEO_RESOLUTION  # 1280 × 720

# Character occupies this fraction of frame height, anchored at top_pad from top
CHAR_HEIGHT_FRAC = 0.88
CHAR_TOP_PAD = int(H * 0.12)  # character top edge: 87px from top of frame

# Face is ~15% down the full-body sprite height → mouth a little lower at ~20%
# absolute y in the frame = CHAR_TOP_PAD + char_pixel_height * MOUTH_FRAC
MOUTH_BODY_FRAC = 0.20   # 20% down the character body = mouth area
MOUTH_W_FRAC   = 0.028   # relative to W
MOUTH_H_FRAC   = 0.018   # relative to H


class VideoAgent:
    def __init__(self) -> None:
        self.logger = setup_logger("video-agent")
        self.image_tool = HFImageGenTool()
        self.bg_removal_tool = ImageBackgroundRemovalTool()

    # ── Audio helpers ──────────────────────────────────────────────────────
    def _get_audio_data(self, audio_path: str) -> Tuple[int, np.ndarray]:
        sr, data = wavfile.read(audio_path)
        if data.ndim > 1:
            data = data.mean(axis=1)
        return sr, data.astype(np.float32)

    def _mouth_open_ratio(self, data: np.ndarray, sr: int, t: float) -> float:
        win = int(0.05 * sr)
        center = int(t * sr)
        s, e = max(0, center - win // 2), min(len(data), center + win // 2)
        chunk = data[s:e]
        if len(chunk) == 0:
            return 0.0
        return float(min(1.0, abs(chunk).mean() / 3000.0))

    # ── Mouth overlay ───────────────────────────────────────────────────────
    def _create_mouth_overlay(self, out_path: Path) -> None:
        """
        Draw the mouth at the correct absolute position on the full-frame canvas.
        Character top is at y=CHAR_TOP_PAD.
        Character pixel height = int(H * CHAR_HEIGHT_FRAC).
        Mouth is MOUTH_BODY_FRAC down the character body.
        """
        char_px_h = int(H * CHAR_HEIGHT_FRAC)
        mouth_abs_y = CHAR_TOP_PAD + int(char_px_h * MOUTH_BODY_FRAC)

        mw = int(W * MOUTH_W_FRAC)
        mh = int(H * MOUTH_H_FRAC)
        mx = (W - mw) // 2  # horizontally centred like the character

        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Outer dark ellipse for depth
        draw.ellipse((mx - 2, mouth_abs_y - 1, mx + mw + 2, mouth_abs_y + mh + 1),
                     fill=(40, 5, 5, 200))
        # Inner bright red mouth
        draw.ellipse((mx, mouth_abs_y, mx + mw, mouth_abs_y + mh),
                     fill=(160, 30, 30, 230))
        img.save(out_path)
        self.logger.info("Mouth overlay at abs_y=%d (char_top=%d, char_h=%d)",
                         mouth_abs_y, CHAR_TOP_PAD, char_px_h)

    # ── Ken-Burns animated background ─────────────────────────────────────
    def _make_animated_bg(self, bg_path: Path, duration: float) -> VideoClip:
        """
        Slow cinematic Ken-Burns pan+zoom. No black borders because we
        pre-scale the image slightly larger than the frame.
        Also applies a subtle vignette + contrast boost for drama.
        """
        MARGIN = 1.08  # 8% extra room for panning
        bg_img = Image.open(bg_path).convert("RGB")

        # Slight contrast/saturation boost for cinematic feel
        bg_img = ImageEnhance.Contrast(bg_img).enhance(1.15)
        bg_img = ImageEnhance.Color(bg_img).enhance(1.1)

        # Scale up to have pan room
        bg_w = int(W * MARGIN)
        bg_h = int(H * MARGIN)
        bg_img = bg_img.resize((bg_w, bg_h), Image.LANCZOS)
        bg_arr = np.array(bg_img, dtype=np.uint8)

        # Vignette mask (darker at edges)
        vig = np.ones((H, W), dtype=np.float32)
        cx, cy = W // 2, H // 2
        for yy in range(H):
            for xx in range(W):
                dx = (xx - cx) / (W / 2)
                dy = (yy - cy) / (H / 2)
                vig[yy, xx] = max(0.5, 1.0 - 0.4 * (dx**2 + dy**2))
        vig_rgb = np.stack([vig, vig, vig], axis=2)  # (H, W, 3)

        def make_frame(t: float) -> np.ndarray:
            p = t / max(duration, 0.001)
            # Pan slowly from top-left toward bottom-right
            ox = int((bg_w - W) * p * 0.6)
            oy = int((bg_h - H) * p * 0.4)
            crop = bg_arr[oy: oy + H, ox: ox + W].astype(np.float32)
            out = np.clip(crop * vig_rgb, 0, 255).astype(np.uint8)
            return out  # (H, W, 3)

        clip = VideoClip(make_frame, duration=duration)
        clip = clip.set_fps(DEFAULT_VIDEO_FPS)
        return clip

    # ── Character sprite helpers ───────────────────────────────────────────
    def _char_clip(self, sprite_path: str, start: float, dur: float) -> ImageClip:
        return (
            ImageClip(sprite_path)
            .set_start(start)
            .set_duration(dur)
            .resize(height=int(H * CHAR_HEIGHT_FRAC))
            .set_position(("center", CHAR_TOP_PAD))
        )

    # ── Main run ───────────────────────────────────────────────────────────
    def run(
        self,
        job_id: str,
        story_spec_data: Dict,
        timing_manifest_data: Dict,
        master_audio_path: str,
    ) -> Dict:
        story  = StorySpec.model_validate(story_spec_data)
        timing = TimingManifest.model_validate(timing_manifest_data)
        root   = Path("data/outputs") / job_id / "video"
        root.mkdir(parents=True, exist_ok=True)

        # ── 1. Generate character sprites once ────────────────────────────
        self.logger.info("Generating character sprites …")
        char_sprites: Dict[str, str] = {}
        for char in story.characters:
            raw = root / f"char_{char.name}_raw.png"
            cut = root / f"char_{char.name}.png"
            self.image_tool.run(
                prompt=(
                    f"full body anime visual novel character, {char.visual_traits}, "
                    "standing neutral pose, centered, pure white background, "
                    "no scenery, high detail, masterpiece"
                ),
                kind="character",
                output_path=str(raw),
            )
            self.bg_removal_tool.run(input_path=str(raw), output_path=str(cut))
            char_sprites[char.name] = str(cut)
            self.logger.info("Sprite ready: %s", char.name)

        # ── 2. Single shared mouth overlay ───────────────────────────────
        mouth_path = root / "mouth_overlay.png"
        self._create_mouth_overlay(mouth_path)

        # ── 3. Build scene clips ─────────────────────────────────────────
        clips: List = []

        for scene in story.scenes:
            self.logger.info("Building scene %s …", scene.scene_id)

            # 3a. Background
            bg_path = root / f"{scene.scene_id}_bg.png"
            self.image_tool.run(
                prompt=(
                    scene.visual_description
                    + ", empty environment, no people, no humans, no characters, "
                    "cinematic anime background art, detailed, atmospheric lighting, "
                    "no text"
                ),
                kind="background",
                output_path=str(bg_path),
            )

            scene_entries = [e for e in timing.entries if e.scene_id == scene.scene_id]
            if not scene_entries:
                self.logger.warning("No timing entries for scene %s, skipping.", scene.scene_id)
                continue

            # ── Scene duration = actual spoken audio, NOT preset value ─────
            scene_start_ms = scene_entries[0].start_ms
            scene_end_ms   = scene_entries[-1].end_ms
            scene_duration = max((scene_end_ms - scene_start_ms) / 1000.0, 1.0)
            self.logger.info("Scene %s duration from audio: %.2fs", scene.scene_id, scene_duration)

            # 3b. Animated background
            bg_clip = self._make_animated_bg(bg_path, scene_duration)

            # 3c. Character + mouth clips
            char_clips:  List = []
            mouth_clips: List = []
            last_end = 0.0

            for entry in scene_entries:
                local_start = max(0.0, (entry.start_ms - scene_start_ms) / 1000.0)
                local_end   = max(local_start + 0.05, (entry.end_ms - scene_start_ms) / 1000.0)

                # Gap before this line: show current speaker silently
                if local_start > last_end + 0.01:
                    char_clips.append(self._char_clip(
                        char_sprites[entry.speaker], last_end, local_start - last_end
                    ))

                # Speaking line clip
                char_clips.append(self._char_clip(
                    char_sprites[entry.speaker], local_start, local_end - local_start
                ))
                last_end = local_end

                # Mouth animation: sample every 80ms during speaking
                sr, audio_data = self._get_audio_data(entry.audio_file)
                t_cur = local_start
                STEP  = 0.08
                while t_cur < local_end:
                    openness = self._mouth_open_ratio(audio_data, sr, t_cur - local_start)
                    dur = min(STEP, local_end - t_cur)
                    if openness > 0.06:
                        mouth_clips.append(
                            ImageClip(str(mouth_path))
                            .set_start(t_cur)
                            .set_duration(dur)
                        )
                    t_cur += STEP

            # Fill tail (silence after last line ends, within scene)
            if last_end < scene_duration:
                tail_speaker = scene_entries[-1].speaker
                char_clips.append(self._char_clip(
                    char_sprites[tail_speaker], last_end, scene_duration - last_end
                ))

            # 3d. Composite: bg → character → mouth
            scene_clip = CompositeVideoClip(
                [bg_clip] + char_clips + mouth_clips,
                size=(W, H),
            ).set_duration(scene_duration)

            clips.append(scene_clip)
            self.logger.info("Scene %s built (%.2fs).", scene.scene_id, scene_duration)

        if not clips:
            raise RuntimeError("No scene clips were produced — check timing manifest.")

        # ── 4. Concatenate and trim to actual audio length ─────────────────
        audio_clip    = AudioFileClip(master_audio_path)
        audio_duration = audio_clip.duration

        final_video = concatenate_videoclips(clips, method="compose")

        # Trim so video ends exactly when dialogue ends
        final_video = final_video.subclip(0, min(final_video.duration, audio_duration))
        final_video = final_video.set_audio(audio_clip.subclip(0, final_video.duration))

        output_path = root / "final_output.mp4"
        final_video.write_videofile(
            str(output_path),
            fps=DEFAULT_VIDEO_FPS,
            codec="libx264",
            audio_codec="aac",
            preset="fast",
            ffmpeg_params=["-crf", "18"],   # high quality encode
            threads=4,
            logger=None,
        )
        self.logger.info("✅ Final video: %s (%.1fs)", output_path, final_video.duration)
        return {"final_video_path": str(output_path)}
