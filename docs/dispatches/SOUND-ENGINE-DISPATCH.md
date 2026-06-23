# SOUND-ENGINE DISPATCH — Procedural Ambient Texture System
> Staged from the main build session 2026-06-23. Fresh session: build this layer.
> When complete, the finished modules slide into `graphparti/sound/` and wire
> into `canvas_widget.py` (event hooks) + `archideck/panel.py` (cockpit hooks).

## The Vision (the architect's words, verbatim)

**"There is no saved track. Each session is continuous. When closed the sounds start
again. Changing a page restarts the sound. This is the ambient texture that will
apply to the social fabric. So you may never hear the previous sounds you liked
ever again. It's all fleeting whispers and the wind."**

This is NOT a music player. This is a **procedural sound design engine** — an
endless, non-repeating ambient texture that responds to everything happening in
the system. No recordings. No loops. No tracks. Pure synthesis + context.

## What It Does

### Layer 1: Ambient Base (the world over the hillside)
- Endless generative ambient drone — warm, evolving, never repeating
- World's fair aesthetic: distant crowd murmur, whispered giggles and laughs
  that appear randomly, fade, never return
- Heart-rate-aligned undertones: subsonic pulses that modulate with context
  (focus = steady, excitement = elevated, rest = slow)
- Lava-lamp quality: smooth, organic, always moving, never jarring

### Layer 2: Input Ripples (keystrokes as instrument strings)
- Every keystroke creates a ripple in the sound — like plucking a string
- Typing pace (APM) modulates the texture: fast typing = denser harmonics,
  slow typing = sparse, contemplative
- Mouse clicks = percussive micro-events (different sounds for different tools)
- Cursor movement = subtle spatial panning
- Settles when still but never stops — breathing room around the musical context
- **Does NOT log or store keystrokes** — events are used like strings on an
  instrument, read and released, never persisted

### Layer 3: Context Modulation (NLP + screen state)
- The NLP parser feeds semantic context to the sound engine
- Drawing architecture = stately, measured, classical undertones
- Writing text = softer, verbal rhythms
- Working on workouts = energetic, pulse-forward
- Browsing/reading = ambient, recessive
- The screen content itself modulates the sound — not just what tool is active,
  but what the content IS

### Layer 4: Tool Feedback (clicks and activations)
- Every tool activation has a sound signature
- Drawing tools: pencil scratch, pen click, compass arc
- Modify tools: mechanical clicks, slide sounds
- The 61 SCL glyph drawers: each glyph has a tonal identity tied to its Diameter
- The zip dial: physical ratchet/click sounds as it spins
- Undo/redo: tape rewind/forward
- Save: satisfying latch/lock

### Layer 5: The Zip Dial Instrument
- The 4-reel zip dial IS a musical instrument
- Spinning the operator dial = 12-note sequence
- Spinning the axis dial = 6-tone chord
- Spinning the order dial = 7-step scale
- Spinning the color dial = 8-timbre palette
- Combined: the zip address IS a musical phrase

## Technical Architecture

### Sound Synthesis Stack
```
Python Layer:
  graphparti/sound/
    engine.py          — SoundEngine: the main loop, mixing, output
    ambient.py         — AmbientGenerator: endless drone + world's-fair texture
    ripple.py          — InputRippleLayer: keystroke/mouse → sound events
    context.py         — ContextModulator: NLP/screen state → parameter shifts
    feedback.py        — ToolFeedbackLayer: click/activate sounds
    instrument.py      — ZipDialInstrument: dial spin → musical phrases
    __init__.py

Libraries to evaluate:
  pyo          — Real-time audio synthesis (C-backed, Python API). Best fit.
                 Oscillators, filters, granular, reverb, FFT, MIDI. Mature.
  sounddevice  — Low-level audio I/O (portaudio wrapper). For raw PCM output.
  numpy        — Generate waveforms as arrays: sin, noise, envelopes.
  scipy.signal — Filters, convolution, spectral analysis.

Fallback (simpler):
  simpleaudio  — Play WAV/numpy arrays. Less control but dead simple.
  pygame.mixer — Basic sound playback. Already common in Python games.
```

### The Engine Loop
```python
class SoundEngine:
    """Main sound engine — runs in a background thread, mixes all layers."""
    
    def __init__(self):
        self.ambient = AmbientGenerator()
        self.ripple = InputRippleLayer()
        self.context = ContextModulator()
        self.feedback = ToolFeedbackLayer()
        self.instrument = ZipDialInstrument()
        self._running = False
    
    def start(self):
        """Start the engine in a background thread."""
        ...
    
    def stop(self):
        """Fade out and stop."""
        ...
    
    def on_keystroke(self, key: str):
        """Called from the main thread on every keypress."""
        self.ripple.pluck(key)
    
    def on_mouse_click(self, x: float, y: float, button: str):
        """Called on mouse events."""
        self.ripple.click(x, y, button)
    
    def on_tool_activate(self, tool_name: str):
        """Called when a tool is activated."""
        self.feedback.activate(tool_name)
    
    def on_context_change(self, context: dict):
        """Called when screen context changes (NLP, content type, mode)."""
        self.context.shift(context)
    
    def on_dial_spin(self, dial: str, value: str):
        """Called when a zip dial reel changes."""
        self.instrument.spin(dial, value)
```

### Docking Points in Graph Parti

These are the exact places in the existing codebase where the sound engine hooks in:

| Hook Point | File | Line | Event |
|------------|------|------|-------|
| Tool activation | `canvas_widget.py` `_activate_tool(key)` | ~636 | `engine.on_tool_activate(key)` |
| Keystroke | `canvas_view.py` `keyPressEvent` | ~836 | `engine.on_keystroke(key)` |
| Mouse click | `canvas_view.py` `mousePressEvent` | ~575 | `engine.on_mouse_click(x, y, btn)` |
| Alt command | `canvas_widget.py` `_on_cmd_enter` | ~813 | `engine.on_tool_activate(resolved_tool)` |
| Layer switch | `canvas_widget.py` `_set_layer_mode` | ~818 | `engine.on_context_change({"layer": mode})` |
| Dial spin | `archideck/panel.py` dial change handlers | various | `engine.on_dial_spin(dial, value)` |
| File save | `canvas_widget.py` `_save` | ~784 | `engine.feedback.save_latch()` |
| Undo/Redo | `canvas_widget.py` undo/redo buttons | ~591 | `engine.feedback.undo()` / `.redo()` |
| App start | `canvas_widget.py` `__init__` end | ~479 | `engine.start()` |
| App close | MainWindow closeEvent | — | `engine.stop()` |

### The Music DNA (from the architect's playlist — Misfire Masquerade)

The aesthetic is defined by these reference points:
- **Moleman** (Misfiring Moleman, Breeze) — glitchy ambient, warm analog drift
- **William Basinski** (Lamentations) — decaying tape loops, beautiful entropy
- **Suzanne Ciani** (The Eighth Wave) — analog synth, Buchla modular, oceanic
- **Nala Sinephro** (Continuum 3, Space 8) — jazz-ambient hybrid, harp + synth pads
- **Blackmill** (Gusto) — melodic ambient, uplifting but never aggressive
- **André 3000** (New Blue Sun) — flute-led ambient, organic, exploratory
- **Goldmund** (Threnody) — piano ambient, minimalist, melancholic warmth
- **Eluvium** (Indoor Swimming, Adolescent Space Adventures) — dense ambient
- **Nicholas Britell** (Agape) — orchestral minimalism, emotional precision
- **Yo-Yo Ma / Goat Rodeo** — acoustic chamber, intricate interplay
- **Ronald Jenkees** (Early Morning May) — electronic warmth, playful
- **A Winged Victory for the Sullen** — post-classical drone, cathedrals of reverb
- **Qlay** (Guts Theme cover) — melancholic guitar, Berserk grief-beauty

**Sonic DNA summary:** warm analog + organic decay + cathedral reverb + occasional
glitch + piano/harp/flute timbres + subsonic pulse + never aggressive, never empty.
The sound of working in a cathedral with the windows open to a world's fair.

### Heart Rate Modulation System

The undertone layer runs at a base frequency tied to resting heart rate (~60 BPM).
Context shifts the target:
- **Focus/drafting:** 60-70 BPM (alpha state, steady)
- **Workout programming:** 80-100 BPM (elevated, energetic)
- **Reading/browsing:** 50-60 BPM (rest, contemplation)
- **Rapid input (high APM):** drift toward 80 BPM (flow state)
- **Idle/still:** drift toward 50 BPM (meditation)

The modulation is gradual — never sudden shifts. Crossfade over 10-30 seconds.
The user shouldn't consciously notice the change; their body responds to the
subsonic undertone while their mind stays on the work.

### Existing Music Notes to Hunt

The architect has music references scattered across the corpus. The fresh session
should grep for these in the canon files:

```
grep -ri "music\|sound\|audio\|ambient\|tone\|frequency\|rhythm\|beat\|pulse" \
  C:\Users\iamja\Desktop\ppl-plus-ultra\archideck/ \
  C:\Users\iamja\Desktop\graph-parti/ \
  --include="*.md" --include="*.parti" --include="*.txt"
```

Also check:
- `Ralph parti.txt` (the architect's voice dump — has sound design references)
- `archideck/CONSTITUTION-COMPOSITION.md` (may have audio/rhythm rules)
- `ppl-plus-ultra/seeds/` (may have sound direction seeds)

## What the Fresh Session Builds

### Phase 1: Core Engine (the minimum viable sound)
1. `graphparti/sound/engine.py` — background thread, audio output via `sounddevice`
2. `graphparti/sound/ambient.py` — basic sine-wave drone + filtered noise + LFO
3. Wire into `canvas_widget.py` — start on app launch, stop on close
4. Test: launch Graph Parti → hear ambient drone → close → silence

### Phase 2: Input Ripples
5. `graphparti/sound/ripple.py` — keystroke → pitched ping, click → percussive tap
6. Wire keyPressEvent and mousePressEvent
7. APM tracking (rolling window, not stored) → modulate ambient density

### Phase 3: Tool Feedback
8. `graphparti/sound/feedback.py` — tool-specific sound signatures
9. The 61 glyph tones (each drawer has a pitch)
10. Undo = tape rewind, Save = latch click

### Phase 4: Context Modulation
11. `graphparti/sound/context.py` — heart rate undertone + semantic modulation
12. Wire to layer switches, content type changes, tool mode

### Phase 5: Zip Dial Instrument
13. `graphparti/sound/instrument.py` — dial spins → musical phrases
14. 12 operator tones × 6 axis chords × 7 order steps × 8 color timbres

## Hard Rules
- **No stored keystrokes.** Events ripple and release. No persistence.
- **No saved tracks.** Every session is unique. Closed = gone forever.
- **No sudden transitions.** Everything crossfades. Lava-lamp dynamics.
- **No silence.** The engine always produces something, even at rest.
- **No aggression.** The loudest moment should feel like a warm room.
- **Context page change = soft restart.** New page, new seed, new texture.

## Sign-off
Staged from the main Graph Parti build session · 2026-06-23 · the sound of
working in a cathedral with the windows open to a world's fair, where you may
never hear the same whisper twice. 🎼
