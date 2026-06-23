"""Procedural ambient texture system — endless, non-repeating, context-responsive."""

try:
    from .engine import SoundEngine
except Exception:

    class SoundEngine:
        """No-op stub when audio libraries aren't available."""

        def start(self):
            pass

        def stop(self):
            pass

        def toggle_mute(self):
            pass

        def on_keystroke(self, key):
            pass

        def on_mouse_click(self, x, y, button):
            pass

        def on_gesture(self, length, angle):
            pass

        def on_tool_activate(self, tool_name):
            pass

        def on_context_change(self, context):
            pass

        def on_dial_spin(self, dial, value):
            pass

        def soft_restart(self):
            pass
