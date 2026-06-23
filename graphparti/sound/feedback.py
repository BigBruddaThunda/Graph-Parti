"""ToolFeedbackLayer — activation sounds, undo/redo, save latch.

Every tool activation, undo, redo, and save gets a synthesized sound signature.
Drawing tools get tonal pings, modify tools get mechanical clicks, specials
get unique effects.
"""
from __future__ import annotations

import numpy as np

_TWO_PI = np.float64(2.0 * np.pi)
_MAX_VOICES = 12

# tool-to-pitch mapping: grouped by function
_DRAW_TOOLS = {
    "line": 523.25, "polyline": 554.37, "rect": 587.33, "circle": 659.26,
    "arc": 698.46, "ellipse": 739.99, "spline": 783.99, "polygon": 830.61,
    "xline": 493.88, "hatch": 440.0,
}
_MODIFY_TOOLS = {
    "trim", "extend", "offset", "fillet", "chamfer", "mirror", "rotate",
    "scale", "stretch", "break_at", "join", "pedit", "matchprop", "divide",
    "copy", "array_rect", "array_polar", "block_save", "block_insert",
}
_TEXT_TOOLS = {"word", "cell", "leader", "dim_linear"}
_MEASURE_TOOLS = {"measure", "eyedropper"}

_TOOL_AMP = 0.08
_TOOL_DECAY = 0.15
_MODIFY_FREQ = 2400.0
_MODIFY_DECAY = 0.02
_TEXT_FREQ = 3200.0
_TEXT_DECAY = 0.015


class _FBVoice:
    __slots__ = ('kind', 'freq', 'freq_end', 'amp', 'decay', 'age', 'alive', 'duration')

    def __init__(self, kind: str, freq: float, amp: float, decay: float,
                 freq_end: float = 0.0, duration: float = 0.0):
        self.kind = kind       # 'tone', 'click', 'sweep', 'latch'
        self.freq = freq
        self.freq_end = freq_end
        self.amp = amp
        self.decay = decay
        self.age = 0.0
        self.alive = True
        self.duration = duration


class ToolFeedbackLayer:

    def __init__(self, sr: int):
        self.sr = sr
        self._voices: list[_FBVoice] = []

    def activate(self, tool_name: str):
        """Tool activation → sound signature."""
        if tool_name in _DRAW_TOOLS:
            freq = _DRAW_TOOLS[tool_name]
            self._voices.append(_FBVoice('tone', freq, _TOOL_AMP, _TOOL_DECAY))
        elif tool_name in _MODIFY_TOOLS:
            self._voices.append(_FBVoice('click', _MODIFY_FREQ, _TOOL_AMP * 0.6, _MODIFY_DECAY))
        elif tool_name in _TEXT_TOOLS:
            self._voices.append(_FBVoice('click', _TEXT_FREQ, _TOOL_AMP * 0.5, _TEXT_DECAY))
        elif tool_name in _MEASURE_TOOLS:
            self._voices.append(_FBVoice('tone', 880.0, _TOOL_AMP * 0.4, 0.1))
        elif tool_name == "select":
            self._voices.append(_FBVoice('click', 1600.0, _TOOL_AMP * 0.4, 0.01))
        elif tool_name == "paint":
            self._voices.append(_FBVoice('tone', 392.0, _TOOL_AMP * 0.7, 0.2))
        elif tool_name == "perspective":
            self._voices.append(_FBVoice('tone', 329.63, _TOOL_AMP * 0.5, 0.25))
        else:
            self._voices.append(_FBVoice('click', 1800.0, _TOOL_AMP * 0.3, 0.015))
        self._trim()

    def undo(self):
        """Tape rewind — falling pitch sweep."""
        self._voices.append(_FBVoice('sweep', 800.0, 0.06, 0.35, freq_end=250.0, duration=0.25))
        self._trim()

    def redo(self):
        """Tape forward — rising pitch sweep."""
        self._voices.append(_FBVoice('sweep', 250.0, 0.06, 0.35, freq_end=800.0, duration=0.25))
        self._trim()

    def save_latch(self):
        """Satisfying lock/latch — percussive click + warm resonance."""
        self._voices.append(_FBVoice('click', 3000.0, 0.07, 0.008))
        self._voices.append(_FBVoice('tone', 523.25, 0.09, 0.4))
        self._trim()

    def render(self, frames: int) -> np.ndarray:
        out = np.zeros(frames, dtype=np.float32)
        if not self._voices:
            return out

        t = np.arange(frames, dtype=np.float64) / self.sr
        dead = []

        for i, v in enumerate(self._voices):
            if not v.alive:
                dead.append(i)
                continue

            age_t = v.age + t
            env = (v.amp * np.exp(-age_t / v.decay)).astype(np.float32)

            if v.kind == 'tone':
                phi = _TWO_PI * v.freq * age_t
                wave = np.sin(phi) * 0.85 + np.sin(2.0 * phi) * 0.15
                out += (wave * env).astype(np.float32)

            elif v.kind == 'click':
                noise = np.random.randn(frames)
                out += (noise * env).astype(np.float32)

            elif v.kind == 'sweep':
                # logarithmic frequency sweep
                if v.duration > 0:
                    progress = np.clip(age_t / v.duration, 0.0, 1.0)
                else:
                    progress = np.ones_like(age_t)
                freq = v.freq * np.exp(progress * np.log(v.freq_end / v.freq))
                phi = _TWO_PI * np.cumsum(freq / self.sr)
                out += (np.sin(phi) * env).astype(np.float32)

            elif v.kind == 'latch':
                phi = _TWO_PI * v.freq * age_t
                out += (np.sin(phi) * env).astype(np.float32)

            v.age += frames / self.sr
            if v.amp * np.exp(-v.age / v.decay) < 0.0003:
                v.alive = False
                dead.append(i)

        for i in reversed(dead):
            self._voices.pop(i)

        return out

    def _trim(self):
        if len(self._voices) > _MAX_VOICES:
            self._voices = self._voices[-_MAX_VOICES:]
