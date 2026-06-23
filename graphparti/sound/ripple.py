"""InputRippleLayer — keystrokes as string plucks, clicks as percussion.

Every input creates a ripple that decays naturally. Typing pace (APM) modulates
the ambient density. No keystrokes are stored — events ripple and release.
"""
from __future__ import annotations

import time
from collections import deque

import numpy as np

_TWO_PI = np.float64(2.0 * np.pi)

# pentatonic scale rooted on A — warm, consonant, never dissonant
_PLUCK_NOTES = [
    220.0, 246.94, 293.66, 329.63, 369.99,   # A3 B3 D4 E4 F#4
    440.0, 493.88, 587.33, 659.26, 739.99,    # A4 B4 D5 E5 F#5
]

_CLICK_FREQ = 1800.0     # percussive click — bright, short
_CLICK_DECAY = 0.004     # very fast decay (seconds)
_PLUCK_DECAY = 0.6       # string ring-out (seconds)
_PLUCK_AMP = 0.08
_CLICK_AMP = 0.05
_MAX_VOICES = 12


class _Voice:
    __slots__ = ('freq', 'phase', 'amp', 'decay', 'age', 'alive', 'is_click')

    def __init__(self, freq: float, amp: float, decay: float, is_click: bool = False):
        self.freq = freq
        self.phase = 0.0
        self.amp = amp
        self.decay = decay
        self.age = 0.0
        self.alive = True
        self.is_click = is_click


class InputRippleLayer:

    def __init__(self, sr: int):
        self.sr = sr
        self._voices: list[_Voice] = []
        self._note_index = 0
        self._apm_times: deque[float] = deque(maxlen=120)
        self._apm = 0.0

    def pluck(self, key: str):
        """Keystroke → pitched ping on the pentatonic scale."""
        freq = _PLUCK_NOTES[self._note_index % len(_PLUCK_NOTES)]
        self._note_index += 1

        # slight random detune for organic feel
        freq *= 1.0 + (np.random.randn() * 0.003)

        v = _Voice(freq, _PLUCK_AMP, _PLUCK_DECAY)
        self._voices.append(v)
        self._trim_voices()

        now = time.monotonic()
        self._apm_times.append(now)
        self._update_apm(now)

    def click(self, x: float, y: float, button: str):
        """Mouse click → short percussive tap."""
        freq = _CLICK_FREQ + np.random.randn() * 200.0
        v = _Voice(freq, _CLICK_AMP, _CLICK_DECAY, is_click=True)
        self._voices.append(v)
        self._trim_voices()

    @property
    def apm(self) -> float:
        """Current actions-per-minute (rolling window, not stored)."""
        return self._apm

    def render(self, frames: int) -> np.ndarray:
        """Render all active voices into a mono float32 buffer."""
        out = np.zeros(frames, dtype=np.float32)
        if not self._voices:
            return out

        t = np.arange(frames, dtype=np.float64) / self.sr
        dead = []

        for i, v in enumerate(self._voices):
            if not v.alive:
                dead.append(i)
                continue

            phi = v.phase + _TWO_PI * v.freq * t

            if v.is_click:
                # noise burst with exponential decay — percussive
                env = v.amp * np.exp(-v.age / v.decay - t / v.decay)
                noise = np.random.randn(frames).astype(np.float64)
                out += (noise * env).astype(np.float32)
            else:
                # damped sine — Karplus-Strong-lite string pluck
                env = v.amp * np.exp(-(v.age + t) / v.decay)
                # add a touch of second harmonic for richness
                wave = np.sin(phi) * 0.8 + np.sin(2.0 * phi) * 0.2
                out += (wave * env).astype(np.float32)

            v.phase = float((phi[-1] + _TWO_PI * v.freq / self.sr) % _TWO_PI)
            v.age += frames / self.sr

            if v.amp * np.exp(-v.age / v.decay) < 0.0005:
                v.alive = False
                dead.append(i)

        for i in reversed(dead):
            self._voices.pop(i)

        return out

    def _trim_voices(self):
        if len(self._voices) > _MAX_VOICES:
            self._voices = self._voices[-_MAX_VOICES:]

    def _update_apm(self, now: float):
        cutoff = now - 10.0
        while self._apm_times and self._apm_times[0] < cutoff:
            self._apm_times.popleft()
        self._apm = len(self._apm_times) * 6.0  # 10-second window → ×6 = per minute
