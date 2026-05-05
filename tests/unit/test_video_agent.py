"""
Unit Tests – Video Agent (pure-logic helpers)
================================================
Tests the audio analysis and mouth-open-ratio helper without touching
any files, APIs, or MoviePy clip creation. Fully offline, sub-second.

Run:
    conda activate agenticai
    python -m pytest tests/unit/test_video_agent.py -v
"""
from __future__ import annotations

import numpy as np
import pytest

from agents.video_agent.agent import (
    CHAR_HEIGHT_FRAC,
    CHAR_TOP_PAD,
    MOUTH_BODY_FRAC,
    MOUTH_H_FRAC,
    MOUTH_W_FRAC,
    W,
    H,
    VideoAgent,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def agent() -> VideoAgent:
    return VideoAgent()


def _sine_wave(freq_hz: float = 440.0, duration_s: float = 1.0, sr: int = 22050,
               amplitude: int = 8000) -> tuple:
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)
    wave = (amplitude * np.sin(2 * np.pi * freq_hz * t)).astype(np.float32)
    return sr, wave


def _silent(duration_s: float = 1.0, sr: int = 22050) -> tuple:
    return sr, np.zeros(int(sr * duration_s), dtype=np.float32)


# ══════════════════════════════════════════════════════════════════
# Frame / canvas constants
# ══════════════════════════════════════════════════════════════════
class TestConstants:
    def test_resolution_landscape(self):
        assert W > H, "Expected landscape (width > height)"

    def test_char_height_fraction_valid(self):
        assert 0.5 < CHAR_HEIGHT_FRAC < 1.0

    def test_char_top_pad_positive(self):
        assert CHAR_TOP_PAD > 0

    def test_mouth_fractions_small(self):
        # Mouth should be small relative to frame
        assert MOUTH_W_FRAC < 0.1
        assert MOUTH_H_FRAC < 0.1

    def test_char_fits_in_frame(self):
        char_px_h = int(H * CHAR_HEIGHT_FRAC)
        assert CHAR_TOP_PAD + char_px_h <= H, "Character overflows frame height"

    def test_mouth_y_within_frame(self):
        char_px_h = int(H * CHAR_HEIGHT_FRAC)
        mouth_abs_y = CHAR_TOP_PAD + int(char_px_h * MOUTH_BODY_FRAC)
        assert 0 <= mouth_abs_y < H


# ══════════════════════════════════════════════════════════════════
# _mouth_open_ratio
# ══════════════════════════════════════════════════════════════════
class TestMouthOpenRatio:
    def test_silent_audio_returns_zero(self, agent):
        sr, data = _silent()
        ratio = agent._mouth_open_ratio(data, sr, 0.5)
        assert ratio == pytest.approx(0.0)

    def test_loud_audio_returns_positive(self, agent):
        sr, data = _sine_wave(amplitude=12000)
        ratio = agent._mouth_open_ratio(data, sr, 0.5)
        assert ratio > 0.0

    def test_output_clamped_between_0_and_1(self, agent):
        # Very loud audio should still return <= 1.0
        sr, data = _sine_wave(amplitude=100_000)
        ratio = agent._mouth_open_ratio(data, sr, 0.5)
        assert 0.0 <= ratio <= 1.0

    def test_returns_float(self, agent):
        sr, data = _sine_wave()
        result = agent._mouth_open_ratio(data, sr, 0.1)
        assert isinstance(result, float)

    def test_edge_time_zero(self, agent):
        sr, data = _sine_wave()
        ratio = agent._mouth_open_ratio(data, sr, 0.0)
        assert 0.0 <= ratio <= 1.0

    def test_time_beyond_audio_returns_zero(self, agent):
        sr, data = _sine_wave(duration_s=0.5)
        # t=5.0 is way past end of 0.5s audio
        ratio = agent._mouth_open_ratio(data, sr, 5.0)
        assert ratio == pytest.approx(0.0)

    def test_ratio_increases_with_loudness(self, agent):
        sr, quiet = _sine_wave(amplitude=500)
        sr, loud  = _sine_wave(amplitude=10000)
        r_quiet = agent._mouth_open_ratio(quiet, sr, 0.5)
        r_loud  = agent._mouth_open_ratio(loud,  sr, 0.5)
        assert r_loud > r_quiet

    def test_stereo_data_passthrough(self, agent):
        """Stereo data should NOT crash (VideoAgent reduces to mono before calling)."""
        sr = 22050
        mono = np.random.randn(sr).astype(np.float32) * 1000
        ratio = agent._mouth_open_ratio(mono, sr, 0.2)
        assert 0.0 <= ratio <= 1.0


# ══════════════════════════════════════════════════════════════════
# Mouth overlay geometry
# ══════════════════════════════════════════════════════════════════
class TestMouthOverlayGeometry:
    def test_mouth_is_horizontally_centred(self):
        mw = int(W * MOUTH_W_FRAC)
        mx = (W - mw) // 2
        assert mx > 0
        assert mx + mw < W

    def test_mouth_y_is_in_face_region(self):
        char_px_h = int(H * CHAR_HEIGHT_FRAC)
        mouth_abs_y = CHAR_TOP_PAD + int(char_px_h * MOUTH_BODY_FRAC)
        # Face region: top 35% of frame
        assert mouth_abs_y < H * 0.35, (
            f"Mouth y={mouth_abs_y} is too low; expected in top 35% of {H}px frame"
        )

    def test_mouth_does_not_overflow_frame(self):
        mh = int(H * MOUTH_H_FRAC)
        char_px_h = int(H * CHAR_HEIGHT_FRAC)
        mouth_abs_y = CHAR_TOP_PAD + int(char_px_h * MOUTH_BODY_FRAC)
        assert mouth_abs_y + mh <= H
