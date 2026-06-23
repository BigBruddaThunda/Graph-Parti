"""ZipDialInstrument — the 4-reel zip dial as a musical instrument.

Spinning the operator dial = 12-note chromatic sequence
Spinning the axis dial = 6-tone whole-tone chord
Spinning the order dial = 7-step Mixolydian scale
Spinning the color dial = 8-timbre palette

Combined: the zip address IS a musical phrase.
"""
from __future__ import annotations

import numpy as np

_TWO_PI = np.float64(2.0 * np.pi)
_MAX_VOICES = 8

# 12 Operators → chromatic scale from C4
_OP_TONES = {
    "📍": 261.63, "🧲": 277.18, "🤌": 293.66, "👀": 311.13,
    "🐋": 329.63, "🧸": 349.23, "🚀": 369.99, "🥨": 392.00,
    "🦢": 415.30, "🦉": 440.00, "🪵": 466.16, "✒️": 493.88,
}

# 6 Axes → whole-tone scale from C4 (open, floating)
_AX_TONES = {
    "🏛": 261.63, "🔨": 293.66, "🌹": 329.63,
    "🪐": 369.99, "⌛": 415.30, "🐬": 466.16,
}

# 7 Orders → Mixolydian scale from A3 (stately, classical)
_OR_TONES = {
    "🐂": 220.00, "⛽": 246.94, "🦋": 277.18, "🏟": 293.66,
    "🌾": 329.63, "⚖": 369.99, "🖼": 392.00,
}

# 8 Colors → timbre index (controls harmonic content)
_CO_TIMBRE = {
    "⚫": 0, "🟢": 1, "🔵": 2, "🟣": 3,
    "🔴": 4, "🟠": 5, "🟡": 6, "⚪": 7,
}

# timbre recipes: (fundamental_weight, 2nd_harm, 3rd_harm, 4th_harm, noise_mix)
_TIMBRES = [
    (0.90, 0.08, 0.02, 0.00, 0.00),  # ⚫ Ordo — pure, dark
    (0.70, 0.20, 0.08, 0.02, 0.00),  # 🟢 Vigor — rich, warm
    (0.80, 0.05, 0.10, 0.05, 0.00),  # 🔵 Tectonics — hollow, flute-like
    (0.60, 0.15, 0.15, 0.10, 0.00),  # 🟣 Rigor — complex, oboe-like
    (0.75, 0.10, 0.05, 0.02, 0.08),  # 🔴 Prioritas — gritty, driven
    (0.85, 0.12, 0.03, 0.00, 0.00),  # 🟠 Koinonia — bright, clear
    (0.65, 0.25, 0.08, 0.02, 0.00),  # 🟡 Mirabilia — golden, bell-like
    (0.95, 0.03, 0.02, 0.00, 0.00),  # ⚪ Otium — airy, near-sine
]

_DIAL_AMP = 0.07
_DIAL_DECAY = 0.8


class _DialVoice:
    __slots__ = ('freq', 'timbre_idx', 'amp', 'decay', 'age', 'alive')

    def __init__(self, freq: float, timbre_idx: int, amp: float, decay: float):
        self.freq = freq
        self.timbre_idx = timbre_idx
        self.amp = amp
        self.decay = decay
        self.age = 0.0
        self.alive = True


class ZipDialInstrument:

    def __init__(self, sr: int):
        self.sr = sr
        self._voices: list[_DialVoice] = []
        self._current_timbre = 0

    def spin(self, dial: str, glyph: str):
        """A dial reel changed — play the corresponding tone."""
        freq = None

        if dial == "operator":
            freq = _OP_TONES.get(glyph)
        elif dial == "axis":
            freq = _AX_TONES.get(glyph)
        elif dial == "order":
            freq = _OR_TONES.get(glyph)
        elif dial == "color":
            idx = _CO_TIMBRE.get(glyph)
            if idx is not None:
                self._current_timbre = idx
            freq = 523.25  # C5 confirmation tone on color change

        if freq is not None:
            v = _DialVoice(freq, self._current_timbre, _DIAL_AMP, _DIAL_DECAY)
            self._voices.append(v)
            if len(self._voices) > _MAX_VOICES:
                self._voices = self._voices[-_MAX_VOICES:]

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
            env = (v.amp * np.exp(-age_t / v.decay)).astype(np.float64)
            timbre = _TIMBRES[v.timbre_idx]

            phi = _TWO_PI * v.freq * age_t
            wave = (
                np.sin(phi) * timbre[0]
                + np.sin(2.0 * phi) * timbre[1]
                + np.sin(3.0 * phi) * timbre[2]
                + np.sin(4.0 * phi) * timbre[3]
            )
            if timbre[4] > 0:
                wave += np.random.randn(frames) * timbre[4]

            out += (wave * env).astype(np.float32)

            v.age += frames / self.sr
            if v.amp * np.exp(-v.age / v.decay) < 0.0003:
                v.alive = False
                dead.append(i)

        for i in reversed(dead):
            self._voices.pop(i)

        return out
