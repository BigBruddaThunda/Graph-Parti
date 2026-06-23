"""ContextModulator — heart-rate undertone + semantic modulation.

The NLP parser, screen state, and layer mode feed context here. The modulator
shifts the ambient character: pulse rate, harmonic color, density. All transitions
crossfade over 10-30 seconds — the user should never consciously notice the shift.
"""
from __future__ import annotations

import numpy as np

_TWO_PI = np.float64(2.0 * np.pi)

# heart-rate targets by context (BPM → Hz)
_HR = {
    "focus":    65 / 60.0,   # alpha state, steady drafting
    "drafting": 65 / 60.0,
    "workout":  90 / 60.0,   # elevated, energetic
    "reading":  55 / 60.0,   # rest, contemplation
    "browsing": 55 / 60.0,
    "idle":     50 / 60.0,   # meditation
    "flow":     75 / 60.0,   # high APM, rapid input
    "default":  60 / 60.0,   # resting heart rate
}

# harmonic color shifts by context — blend factors for additional overtones
_HARMONIC_COLOR = {
    "parti":  {"brightness": 0.6, "warmth": 0.8},   # stately, measured
    "trace":  {"brightness": 0.3, "warmth": 0.9},   # soft, contemplative
    "book":   {"brightness": 0.5, "warmth": 0.7},   # balanced
    "both":   {"brightness": 0.4, "warmth": 0.75},
}

_SLEW_RATE = 0.02  # how fast parameters converge per render block (~0.5 Hz)


class ContextModulator:

    def __init__(self, sr: int):
        self.sr = sr
        self._pulse_freq = _HR["default"]
        self._target_pulse = _HR["default"]
        self._pulse_phase = 0.0

        self._brightness = 0.5
        self._target_brightness = 0.5
        self._warmth = 0.8
        self._target_warmth = 0.8

        self._density = 1.0
        self._target_density = 1.0

    def shift(self, context: dict):
        """Accept a context dict and update targets. Called from main thread."""
        if "layer" in context:
            layer = context["layer"]
            color = _HARMONIC_COLOR.get(layer, _HARMONIC_COLOR["parti"])
            self._target_brightness = color["brightness"]
            self._target_warmth = color["warmth"]

        if "mode" in context:
            mode = context["mode"]
            self._target_pulse = _HR.get(mode, _HR["default"])

        if "apm" in context:
            apm = context["apm"]
            if apm > 120:
                self._target_pulse = _HR["flow"]
                self._target_density = min(1.5, 1.0 + apm / 400.0)
            elif apm < 10:
                self._target_pulse = _HR["idle"]
                self._target_density = 0.7
            else:
                self._target_density = 1.0

    def render(self, frames: int) -> tuple[np.ndarray, float, float]:
        """Render the context modulation layer.

        Returns (pulse_signal, brightness, warmth) where pulse_signal is a
        mono float32 array and brightness/warmth are current parameter values
        that other layers can use to adjust their character.
        """
        dt = frames / self.sr

        # slew all parameters toward targets
        self._pulse_freq += _SLEW_RATE * (self._target_pulse - self._pulse_freq) * dt * 60
        self._brightness += _SLEW_RATE * (self._target_brightness - self._brightness) * dt * 60
        self._warmth += _SLEW_RATE * (self._target_warmth - self._warmth) * dt * 60
        self._density += _SLEW_RATE * (self._target_density - self._density) * dt * 60

        # subsonic heart-rate pulse
        t = np.arange(frames, dtype=np.float64) / self.sr
        phi = self._pulse_phase + _TWO_PI * self._pulse_freq * t
        pulse = (np.sin(phi) * 0.018 * self._density).astype(np.float32)
        self._pulse_phase = float((phi[-1] + _TWO_PI * self._pulse_freq / self.sr) % _TWO_PI)

        return pulse, self._brightness, self._warmth

    @property
    def density(self) -> float:
        return self._density
