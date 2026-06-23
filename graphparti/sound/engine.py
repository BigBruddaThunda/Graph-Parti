"""SoundEngine — background audio thread, layer mixing, output.

Runs a sounddevice OutputStream whose callback renders all active layers,
applies master volume with smooth fade, and writes stereo float32 to the DAC.
"""
from __future__ import annotations

import logging
import threading

import numpy as np
import sounddevice as sd

from .ambient import AmbientGenerator
from .context import ContextModulator
from .feedback import ToolFeedbackLayer
from .instrument import ZipDialInstrument
from .ripple import InputRippleLayer

log = logging.getLogger(__name__)

_SAMPLE_RATE = 44100
_BLOCK_SIZE = 1024
_CHANNELS = 2
_FADE_SECONDS = 3.0
_MASTER_VOLUME = 0.48
_CROSSFEED = 0.12


class SoundEngine:

    def __init__(self):
        self._running = False
        self._stream: sd.OutputStream | None = None
        self._volume = 0.0
        self._target_volume = _MASTER_VOLUME
        self._muted = False
        self._pre_mute_volume = _MASTER_VOLUME
        self.ambient = AmbientGenerator(_SAMPLE_RATE)
        self.ripple = InputRippleLayer(_SAMPLE_RATE)
        self.feedback = ToolFeedbackLayer(_SAMPLE_RATE)
        self.context = ContextModulator(_SAMPLE_RATE)
        self.instrument = ZipDialInstrument(_SAMPLE_RATE)

    # ── lifecycle ────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        try:
            self._running = True
            self._volume = 0.0
            self._target_volume = _MASTER_VOLUME
            self.ambient.reseed()
            self._stream = sd.OutputStream(
                samplerate=_SAMPLE_RATE,
                blocksize=_BLOCK_SIZE,
                channels=_CHANNELS,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
            log.info("sound engine started")
        except Exception as exc:
            log.warning("sound engine failed to start: %s", exc)
            self._running = False

    def stop(self):
        if not self._running:
            return
        self._target_volume = 0.0
        threading.Timer(_FADE_SECONDS + 0.5, self._shutdown).start()

    def _shutdown(self):
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        log.info("sound engine stopped")

    def toggle_mute(self):
        if self._muted:
            self._muted = False
            self._target_volume = self._pre_mute_volume
        else:
            self._pre_mute_volume = self._target_volume
            self._muted = True
            self._target_volume = 0.0

    def soft_restart(self):
        """New seed, same stream — called on context/page change."""
        self.ambient.reseed()

    # ── input events ───────────────────────────────────────────────

    def on_keystroke(self, key: str):
        self.ripple.pluck(key)

    def on_mouse_click(self, x: float, y: float, button: str):
        self.ripple.click(x, y, button)

    def on_gesture(self, length: float, angle: float):
        self.ambient.on_gesture(length, angle)

    def on_tool_activate(self, tool_name: str):
        self.feedback.activate(tool_name)

    def on_context_change(self, context: dict):
        self.context.shift(context)

    def on_dial_spin(self, dial: str, value: str):
        self.instrument.spin(dial, value)

    # ── audio callback ───────────────────────────────────────────────

    def _callback(self, outdata: np.ndarray, frames: int, time_info, status):
        if not self._running:
            outdata.fill(0)
            return

        left, right = self.ambient.render(frames)

        # context modulation (heart-rate pulse + parameter shifts)
        ctx_pulse, brightness, warmth = self.context.render(frames)
        left += ctx_pulse
        right += ctx_pulse

        # feed APM back into context
        apm = self.ripple.apm
        if apm > 0:
            self.context.shift({"apm": apm})

        # input ripples + tool feedback + dial instrument (mono, panned center)
        ripples = self.ripple.render(frames)
        fb = self.feedback.render(frames)
        dial = self.instrument.render(frames)
        mono_layers = ripples + fb + dial
        left += mono_layers
        right += mono_layers

        # stereo cross-feed for cohesion
        mix_l = left * (1.0 - _CROSSFEED) + right * _CROSSFEED
        mix_r = right * (1.0 - _CROSSFEED) + left * _CROSSFEED

        gain = self._gain_ramp(frames)
        mix_l *= gain
        mix_r *= gain

        # soft clip — prevents harsh distortion, preserves warmth
        outdata[:, 0] = np.tanh(mix_l)
        outdata[:, 1] = np.tanh(mix_r)

    def _gain_ramp(self, frames: int) -> np.ndarray | np.float32:
        """Per-sample volume ramp for click-free fades."""
        start = self._volume
        target = self._target_volume
        if abs(start - target) < 1e-5:
            return np.float32(start)

        step = 1.0 / (_SAMPLE_RATE * _FADE_SECONDS)
        direction = 1.0 if target > start else -1.0
        ramp = start + direction * step * np.arange(frames, dtype=np.float32)

        if direction > 0:
            np.minimum(ramp, target, out=ramp)
        else:
            np.maximum(ramp, target, out=ramp)

        self._volume = float(ramp[-1])
        return ramp
