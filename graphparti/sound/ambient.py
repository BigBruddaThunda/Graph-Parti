"""AmbientGenerator — evolving soundscape, not a static drone.

The sound of working in a cathedral with the windows open to a world's fair.
Chord progressions that drift through warm voicings. Wind that breathes.
Birds, whispers, rustling leaves, distant laughter that appear once and
vanish forever. Drawing gestures shape the future texture.
"""
from __future__ import annotations

import math

import numpy as np

_TWO_PI = np.float64(2.0 * np.pi)

# ── chord voicings — warm, open, ambient ─────────────────────────────
# Each voicing: (sub, root, color, high) — open-spaced for cathedral depth
_VOICINGS = [
    (55.0, 110.0, 164.81, 246.94),     # Am9 — dreamy, wide
    (65.41, 130.81, 196.0, 246.94),     # Cmaj7 — bright, hopeful
    (82.41, 164.81, 246.94, 369.99),    # Em — melancholic warmth
    (73.42, 146.83, 220.0, 329.63),     # Dm9 — mysterious
    (87.31, 174.61, 261.63, 329.63),    # Fmaj7 — pastoral
    (49.0, 98.0, 146.83, 196.0),        # Gsus2 — open, suspended
    (55.0, 110.0, 138.59, 220.0),       # A — major warmth, resolution
]

_LFO_FREQS = [0.031, 0.067, 0.127, 0.199]

# ── texture event types ──────────────────────────────────────────────
_EVT_BIRD = 0
_EVT_LEAF = 1
_EVT_WHISPER = 2
_EVT_LAUGH = 3
_EVT_DRIP = 4
_EVT_CROWD = 5

_EVT_WEIGHTS = [0.25, 0.18, 0.18, 0.12, 0.12, 0.15]
_EVT_TYPES = [_EVT_BIRD, _EVT_LEAF, _EVT_WHISPER, _EVT_LAUGH, _EVT_DRIP, _EVT_CROWD]

# vowel formant centers (Hz) for whisper/laugh synthesis
_FORMANTS = [
    (730, 1090, 2440),    # a
    (530, 1840, 2480),    # e
    (270, 2290, 3010),    # i
    (570, 840, 2410),     # o
    (440, 1020, 2240),    # u
]


# ═════════════════════════════════════════════════════════════════════
class _GlidingOsc:
    """Oscillator that glides smoothly between target frequencies."""

    __slots__ = ('freq', 'target', 'phase', 'amp', 'sr', '_drift',
                 '_glide_rate', '_detune')

    def __init__(self, freq: float, amp: float, sr: int, detune: float = 0.0):
        self.freq = freq + detune
        self.target = self.freq
        self.phase = np.random.uniform(0, _TWO_PI)
        self.amp = amp
        self.sr = sr
        self._drift = 0.0
        self._glide_rate = 0.015     # exponential glide speed
        self._detune = detune

    def set_target(self, freq: float):
        self.target = freq + self._detune

    def reset(self):
        self.phase = np.random.uniform(0, _TWO_PI)
        self._drift = 0.0

    def render(self, frames: int) -> np.ndarray:
        dt = frames / self.sr

        # glide toward target (exponential approach — smooth, never sudden)
        self.freq += (self.target - self.freq) * self._glide_rate

        # OU frequency drift on top of glide
        theta, sigma = 0.3, self.freq * 0.002
        self._drift += theta * -self._drift * dt + sigma * math.sqrt(dt) * np.random.randn()
        actual_freq = self.freq + self._drift

        t = np.arange(frames, dtype=np.float64) / self.sr
        phi = self.phase + _TWO_PI * actual_freq * t
        wave = np.sin(phi) * 0.82 + np.sin(2.0 * phi) * 0.14 + np.sin(3.0 * phi) * 0.04
        self.phase = float((phi[-1] + _TWO_PI * actual_freq / self.sr) % _TWO_PI)
        return (wave * self.amp).astype(np.float32)


# ═════════════════════════════════════════════════════════════════════
class _EvolvingDrone:
    """Harmonic progressions — the drone shifts through chord voicings."""

    def __init__(self, sr: int):
        self.sr = sr
        self._chord_idx = 0
        self._chord_timer = 0.0
        self._chord_dur = 35.0 + np.random.random() * 25.0

        v = _VOICINGS[0]
        amps = (0.12, 0.20, 0.10, 0.06)
        self._oscs_l = [_GlidingOsc(v[i], amps[i], sr) for i in range(4)]
        self._oscs_r = [_GlidingOsc(v[i], amps[i], sr,
                                     detune=[0.3, 0.4, -0.3, 0.5][i])
                        for i in range(4)]

    def reseed(self):
        self._chord_idx = int(np.random.random() * len(_VOICINGS))
        self._chord_timer = 0.0
        self._chord_dur = 35.0 + np.random.random() * 25.0
        self._apply_voicing(self._chord_idx)
        for osc in self._oscs_l + self._oscs_r:
            osc.reset()

    def nudge(self, length: float, angle: float):
        """Drawing gesture nudges the progression forward."""
        if length > 100:
            self._chord_timer += length / 50.0

    def render(self, frames: int) -> tuple[np.ndarray, np.ndarray]:
        self._chord_timer += frames / self.sr
        if self._chord_timer >= self._chord_dur:
            self._chord_timer = 0.0
            self._chord_dur = 35.0 + np.random.random() * 25.0
            self._chord_idx = (self._chord_idx + 1) % len(_VOICINGS)
            self._apply_voicing(self._chord_idx)

        left = np.zeros(frames, dtype=np.float32)
        right = np.zeros(frames, dtype=np.float32)
        for osc in self._oscs_l:
            left += osc.render(frames)
        for osc in self._oscs_r:
            right += osc.render(frames)
        return left, right

    def _apply_voicing(self, idx: int):
        v = _VOICINGS[idx]
        for i, osc in enumerate(self._oscs_l):
            osc.set_target(v[i])
        for i, osc in enumerate(self._oscs_r):
            osc.set_target(v[i])


# ═════════════════════════════════════════════════════════════════════
class _WindLayer:
    """Continuous wind — filtered noise with evolving cutoff and gusts."""

    def __init__(self, sr: int):
        self.sr = sr
        self._cutoff = 350.0
        self._target_cutoff = 350.0
        self._base_cutoff = 350.0
        self._intensity = 0.030
        self._target_intensity = 0.030
        self._s1l = self._s2l = 0.0
        self._s1r = self._s2r = 0.0
        # whistle: narrow resonant band
        self._whistle_freq = 600.0
        self._whistle_phase = 0.0
        self._whistle_amp = 0.0
        self._whistle_target = 0.0

    def reseed(self):
        self._s1l = self._s2l = 0.0
        self._s1r = self._s2r = 0.0
        self._cutoff = 350.0
        self._target_cutoff = 350.0
        self._whistle_amp = 0.0
        self._whistle_target = 0.0

    def gust(self, strength: float):
        """Trigger a wind gust — strength 0.0 to 1.0."""
        self._target_cutoff = min(2500, self._base_cutoff + strength * 1200)
        self._target_intensity = min(0.08, 0.030 + strength * 0.04)
        if strength > 0.5:
            self._whistle_target = 0.008 * strength
            self._whistle_freq = 500 + np.random.random() * 800

    def render(self, frames: int) -> tuple[np.ndarray, np.ndarray]:
        # parameter slew
        rate = 0.008
        self._cutoff += rate * (self._target_cutoff - self._cutoff)
        self._target_cutoff += 0.003 * (self._base_cutoff - self._target_cutoff)
        self._intensity += rate * (self._target_intensity - self._intensity)
        self._target_intensity += 0.003 * (0.030 - self._target_intensity)
        self._whistle_amp += 0.01 * (self._whistle_target - self._whistle_amp)
        self._whistle_target *= 0.995

        alpha = np.float64(min(0.5, _TWO_PI * self._cutoff / self.sr))

        noise_l = np.random.randn(frames).astype(np.float64) * self._intensity
        noise_r = np.random.randn(frames).astype(np.float64) * self._intensity
        out_l = np.empty(frames, dtype=np.float32)
        out_r = np.empty(frames, dtype=np.float32)

        s1l, s2l = self._s1l, self._s2l
        s1r, s2r = self._s1r, self._s2r
        for i in range(frames):
            s1l += alpha * (noise_l[i] - s1l)
            s2l += alpha * (s1l - s2l)
            out_l[i] = s2l
            s1r += alpha * (noise_r[i] - s1r)
            s2r += alpha * (s1r - s2r)
            out_r[i] = s2r
        self._s1l, self._s2l = s1l, s2l
        self._s1r, self._s2r = s1r, s2r

        # wind whistle (narrow resonance)
        if self._whistle_amp > 0.001:
            t = np.arange(frames, dtype=np.float64) / self.sr
            phi = self._whistle_phase + _TWO_PI * self._whistle_freq * t
            whistle = (np.sin(phi) * self._whistle_amp).astype(np.float32)
            self._whistle_phase = float(phi[-1] % _TWO_PI)
            out_l += whistle
            out_r += whistle * 0.7   # slightly off-center

        return out_l, out_r


# ═════════════════════════════════════════════════════════════════════
class _TextureEvent:
    """Pre-rendered sound event — read from a buffer, stereo positioned."""
    __slots__ = ('buf', 'pos', 'alive', 'gain_l', 'gain_r')

    def __init__(self, buf: np.ndarray, pan: float = 0.0):
        self.buf = buf
        self.pos = 0
        self.alive = True
        self.gain_l = np.float32(math.sqrt(0.5 * (1.0 - pan)))
        self.gain_r = np.float32(math.sqrt(0.5 * (1.0 + pan)))

    def read(self, frames: int) -> tuple[np.ndarray, np.ndarray]:
        remaining = len(self.buf) - self.pos
        if remaining <= 0:
            self.alive = False
            z = np.zeros(frames, dtype=np.float32)
            return z, z
        n = min(frames, remaining)
        out = np.zeros(frames, dtype=np.float32)
        out[:n] = self.buf[self.pos:self.pos + n]
        self.pos += n
        if self.pos >= len(self.buf):
            self.alive = False
        return out * self.gain_l, out * self.gain_r


class _TextureScheduler:
    """Spawns and manages short-lived natural sound events."""

    def __init__(self, sr: int):
        self.sr = sr
        self._events: list[_TextureEvent] = []
        self._timer = 0.0
        self._interval = 4.0 + np.random.random() * 6.0
        self._boost = 1.0
        self._max_events = 6

    def clear(self):
        self._events.clear()
        self._timer = 0.0
        self._interval = 4.0 + np.random.random() * 6.0

    def boost(self, amount: float):
        """Temporarily increase spawn density."""
        self._boost = min(3.0, self._boost + amount)

    def render(self, frames: int) -> tuple[np.ndarray, np.ndarray]:
        dt = frames / self.sr
        self._timer += dt
        self._boost = max(1.0, self._boost - dt * 0.1)

        if self._timer >= self._interval / self._boost:
            self._timer = 0.0
            self._interval = 4.0 + np.random.random() * 8.0
            if len(self._events) < self._max_events:
                self._spawn()

        left = np.zeros(frames, dtype=np.float32)
        right = np.zeros(frames, dtype=np.float32)
        dead = []
        for i, evt in enumerate(self._events):
            if not evt.alive:
                dead.append(i)
                continue
            el, er = evt.read(frames)
            left += el
            right += er
            if not evt.alive:
                dead.append(i)
        for i in reversed(dead):
            self._events.pop(i)
        return left, right

    def _spawn(self):
        kind = np.random.choice(_EVT_TYPES, p=_EVT_WEIGHTS)
        pan = np.random.uniform(-0.7, 0.7)
        buf = None

        if kind == _EVT_BIRD:
            buf = self._make_bird()
        elif kind == _EVT_LEAF:
            buf = self._make_leaf()
        elif kind == _EVT_WHISPER:
            buf = self._make_whisper()
        elif kind == _EVT_LAUGH:
            buf = self._make_laugh()
        elif kind == _EVT_DRIP:
            buf = self._make_drip()
        elif kind == _EVT_CROWD:
            buf = self._make_crowd()

        if buf is not None:
            self._events.append(_TextureEvent(buf, pan))

    # ── sound factories (all vectorized, no per-sample loops) ────────

    def _make_bird(self) -> np.ndarray:
        sr = self.sr
        chirps = 1 + int(np.random.random() * 3)
        parts = []
        for _ in range(chirps):
            dur = 0.05 + np.random.random() * 0.15
            n = int(sr * dur)
            t = np.arange(n, dtype=np.float64) / sr
            f0 = 2500 + np.random.random() * 4000
            f1 = f0 * (0.6 + np.random.random() * 0.8)
            freq = np.linspace(f0, f1, n)
            phi = np.cumsum(_TWO_PI * freq / sr)
            env = np.exp(-t * (12 + np.random.random() * 20))
            parts.append((np.sin(phi) * env * 0.018).astype(np.float32))
            gap = int(sr * (0.03 + np.random.random() * 0.08))
            parts.append(np.zeros(gap, dtype=np.float32))
        return np.concatenate(parts)

    def _make_leaf(self) -> np.ndarray:
        sr = self.sr
        dur = 0.3 + np.random.random() * 0.8
        n = int(sr * dur)
        noise = np.random.randn(n)
        # bandpass via FFT (2000-7000 Hz)
        spec = np.fft.rfft(noise)
        freqs = np.fft.rfftfreq(n, 1.0 / sr)
        mask = np.exp(-0.5 * ((freqs - 4000) / 1500) ** 2)
        spec *= mask
        filtered = np.fft.irfft(spec, n)
        # crackling envelope (rapid random AM)
        am = np.random.uniform(0.2, 1.0, size=n // 64 + 1)
        am = np.repeat(am, 64)[:n]
        env = np.sin(np.linspace(0, np.pi, n)) ** 2
        return (filtered * am * env * 0.012).astype(np.float32)

    def _make_whisper(self) -> np.ndarray:
        sr = self.sr
        dur = 0.4 + np.random.random() * 0.8
        n = int(sr * dur)
        noise = np.random.randn(n)
        spec = np.fft.rfft(noise)
        freqs = np.fft.rfftfreq(n, 1.0 / sr)
        # formant envelope from random vowel
        f1, f2, f3 = _FORMANTS[int(np.random.random() * len(_FORMANTS))]
        bw = 120
        formant = (
            np.exp(-0.5 * ((freqs - f1) / bw) ** 2) * 0.5
            + np.exp(-0.5 * ((freqs - f2) / bw) ** 2) * 0.35
            + np.exp(-0.5 * ((freqs - f3) / bw) ** 2) * 0.15
        )
        spec *= formant
        shaped = np.fft.irfft(spec, n)
        # syllable envelope (1-3 syllables)
        syllables = 1 + int(np.random.random() * 2)
        env = np.zeros(n, dtype=np.float64)
        syl_n = n // syllables
        for s in range(syllables):
            a, b = s * syl_n, min((s + 1) * syl_n, n)
            env[a:b] = np.sin(np.linspace(0, np.pi, b - a)) ** 2
        return (shaped * env * 0.010).astype(np.float32)

    def _make_laugh(self) -> np.ndarray:
        sr = self.sr
        dur = 0.5 + np.random.random() * 1.0
        n = int(sr * dur)
        noise = np.random.randn(n)
        spec = np.fft.rfft(noise)
        freqs = np.fft.rfftfreq(n, 1.0 / sr)
        f1, f2, f3 = _FORMANTS[0]   # 'a' vowel — open laugh
        bw = 150
        formant = (
            np.exp(-0.5 * ((freqs - f1) / bw) ** 2) * 0.5
            + np.exp(-0.5 * ((freqs - f2) / bw) ** 2) * 0.3
            + np.exp(-0.5 * ((freqs - f3) / bw) ** 2) * 0.2
        )
        spec *= formant
        shaped = np.fft.irfft(spec, n)
        # ha-ha-ha rhythmic modulation
        t = np.arange(n, dtype=np.float64) / sr
        ha_rate = 5.0 + np.random.random() * 4.0
        mod = (0.4 + 0.6 * np.sin(_TWO_PI * ha_rate * t)) ** 3
        env = np.sin(np.linspace(0, np.pi, n)) ** 1.5
        return (shaped * mod * env * 0.008).astype(np.float32)

    def _make_drip(self) -> np.ndarray:
        sr = self.sr
        dur = 0.08 + np.random.random() * 0.15
        n = int(sr * dur)
        t = np.arange(n, dtype=np.float64) / sr
        freq = 800 + np.random.random() * 1200
        env = np.exp(-t * (20 + np.random.random() * 30))
        # sine + slight frequency drop (water resonance)
        f_sweep = freq * np.exp(-t * 3)
        phi = np.cumsum(_TWO_PI * f_sweep / sr)
        return (np.sin(phi) * env * 0.020).astype(np.float32)

    def _make_crowd(self) -> np.ndarray:
        sr = self.sr
        dur = 2.0 + np.random.random() * 2.5
        n = int(sr * dur)
        noise = np.random.randn(n)
        spec = np.fft.rfft(noise)
        freqs = np.fft.rfftfreq(n, 1.0 / sr)
        # broad vocal band (300-3000 Hz)
        mask = np.exp(-0.5 * ((freqs - 1200) / 800) ** 2)
        spec *= mask
        crowd = np.fft.irfft(spec, n)
        # swell envelope — rises, crests, fades
        env = np.sin(np.linspace(0, np.pi, n)) ** 2
        return (crowd * env * 0.015).astype(np.float32)


# ═════════════════════════════════════════════════════════════════════
class AmbientGenerator:
    """Evolving ambient soundscape — drone progressions, wind, natural textures."""

    def __init__(self, sr: int):
        self.sr = sr
        self._drone = _EvolvingDrone(sr)
        self._wind = _WindLayer(sr)
        self._textures = _TextureScheduler(sr)

        self._lfo_phases = [np.random.uniform(0, _TWO_PI) for _ in _LFO_FREQS]
        self._pulse_freq = 1.0
        self._pulse_phase = np.random.uniform(0, _TWO_PI)

    def reseed(self):
        self._drone.reseed()
        self._wind.reseed()
        self._textures.clear()
        self._lfo_phases = [np.random.uniform(0, _TWO_PI) for _ in _LFO_FREQS]
        self._pulse_phase = np.random.uniform(0, _TWO_PI)

    def on_gesture(self, length: float, angle: float):
        """Drawing gesture shapes the soundscape."""
        self._drone.nudge(length, angle)
        self._wind.gust(min(1.0, length / 500.0))
        self._textures.boost(min(2.0, length / 200.0))

    def render(self, frames: int) -> tuple[np.ndarray, np.ndarray]:
        t = np.arange(frames, dtype=np.float64) / self.sr

        # LFO breathing (additive, not multiplicative)
        lfo_sum = np.zeros(frames, dtype=np.float32)
        for i, freq in enumerate(_LFO_FREQS):
            phi = self._lfo_phases[i] + _TWO_PI * freq * t
            lfo_sum += np.sin(phi).astype(np.float32)
            self._lfo_phases[i] = float((phi[-1] + _TWO_PI * freq / self.sr) % _TWO_PI)
        lfo = (0.82 + 0.18 * lfo_sum / len(_LFO_FREQS)).astype(np.float32)

        # evolving drone
        drone_l, drone_r = self._drone.render(frames)
        drone_l *= lfo
        drone_r *= lfo

        # wind
        wind_l, wind_r = self._wind.render(frames)

        # texture events (birds, whispers, leaves, etc.)
        tex_l, tex_r = self._textures.render(frames)

        # subsonic heart pulse
        phi = self._pulse_phase + _TWO_PI * self._pulse_freq * t
        pulse = (np.sin(phi) * 0.018).astype(np.float32)
        self._pulse_phase = float((phi[-1] + _TWO_PI * self._pulse_freq / self.sr) % _TWO_PI)

        left = drone_l + wind_l + tex_l + pulse
        right = drone_r + wind_r + tex_r + pulse
        return left, right
