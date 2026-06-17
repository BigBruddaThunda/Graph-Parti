"""Viewport navigation system for GRAPH PARTI.

One movement grammar, many input surfaces: joystick, arrow keys, z-pad.

Two modes tied to the wireframe toggle:
  Grid ON  → cell-stepped, orthogonal (tile-based: RPG / puzzle / grid builder)
  Grid OFF → smooth, analog, free (free-roam: platformer / flight / freehand)

Dead zone is mapped to D (1 grid cell), so pushing past the dead zone
commits to at least a 1-cell step. The joystick IS the grid.

Joystick reads via Windows Multimedia API (winmm.dll) — zero dependencies.
Only active when the Graph Parti window has focus.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import math

from PySide6.QtCore import QObject, QTimer


# ── Windows Multimedia joystick API ──
try:
    _winmm = ctypes.WinDLL("winmm", use_last_error=True)
except OSError:
    _winmm = None


class _JOYINFOEX(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("dwFlags", wt.DWORD),
        ("dwXpos", wt.DWORD),
        ("dwYpos", wt.DWORD),
        ("dwZpos", wt.DWORD),
        ("dwRpos", wt.DWORD),
        ("dwUpos", wt.DWORD),
        ("dwVpos", wt.DWORD),
        ("dwButtons", wt.DWORD),
        ("dwButtonNumber", wt.DWORD),
        ("dwPOV", wt.DWORD),
        ("dwReserved1", wt.DWORD),
        ("dwReserved2", wt.DWORD),
    ]


_JOY_RETURNALL = 0xFF
_JOYERR_NOERROR = 0
_MID = 32767


def _read_joy(joy_id: int = 0) -> _JOYINFOEX | None:
    if _winmm is None:
        return None
    info = _JOYINFOEX()
    info.dwSize = ctypes.sizeof(_JOYINFOEX)
    info.dwFlags = _JOY_RETURNALL
    if _winmm.joyGetPosEx(joy_id, ctypes.byref(info)) == _JOYERR_NOERROR:
        return info
    return None


def joystick_available(joy_id: int = 0) -> bool:
    return _read_joy(joy_id) is not None


# ═══════════════════════════════════════════════════════════
# ViewNavigator — the shared movement system
# ═══════════════════════════════════════════════════════════

class ViewNavigator(QObject):
    """Unified viewport movement. All input surfaces call step() or push().

    step(dx, dy)  — cell-based: move exactly dx/dy cells. Arrow keys, z-pad.
    push(x, y)    — analog: continuous -1..1 input. Joystick stick axes.
    zoom(delta)    — analog zoom. Joystick z-axis.

    Internally, push() routes to grid-step or free-scroll based on wireframe state.
    """

    def __init__(self, canvas_view, parent=None) -> None:
        super().__init__(parent or canvas_view)
        self._view = canvas_view
        self._accum_x = 0.0
        self._accum_y = 0.0

    def step(self, dx_cells: int, dy_cells: int) -> None:
        """Move viewport by exact cell count. Grid-on or off, this always
        steps in cell-sized increments."""
        gs = self._view.grid_spacing
        zoom = self._view.transform().m11()
        hbar = self._view.horizontalScrollBar()
        vbar = self._view.verticalScrollBar()
        hbar.setValue(int(hbar.value() + dx_cells * gs * zoom))
        vbar.setValue(int(vbar.value() + dy_cells * gs * zoom))

    def push(self, x: float, y: float) -> None:
        """Analog input (-1..1 per axis). Grid-on → cell-step accumulator.
        Grid-off → smooth scroll."""
        grid_on = getattr(self._view, '_wireframe', True)
        if grid_on:
            self._push_grid(x, y)
        else:
            self._push_free(x, y)

    def _push_grid(self, x: float, y: float) -> None:
        """Cell-stepping: accumulate input, orthogonal lock on dominant axis,
        step when a full cell is reached."""
        mag = math.hypot(x, y)
        if mag < 1e-6:
            self._accum_x *= 0.5
            self._accum_y *= 0.5
            return

        # Orthogonal lock: only the dominant axis gets input
        if abs(x) >= abs(y):
            y = 0.0
        else:
            x = 0.0

        # Rate scales with deflection: gentle = slow step, full tilt = fast
        rate = 0.06 + abs(x if x != 0 else y) * 0.18
        self._accum_x += x * rate
        self._accum_y += y * rate

        dx = int(self._accum_x)
        dy = int(self._accum_y)
        if dx != 0:
            self._accum_x -= dx
        if dy != 0:
            self._accum_y -= dy
        if dx != 0 or dy != 0:
            self.step(dx, dy)

    def _push_free(self, x: float, y: float) -> None:
        """Smooth analog scroll — quadratic curve for precision at low tilt."""
        mag = math.hypot(x, y)
        if mag < 1e-6:
            return
        curve = mag * mag
        fx = x / mag * curve
        fy = y / mag * curve
        speed = 14.0 / max(self._view.transform().m11(), 0.05)
        hbar = self._view.horizontalScrollBar()
        vbar = self._view.verticalScrollBar()
        hbar.setValue(int(hbar.value() + fx * speed))
        vbar.setValue(int(vbar.value() + fy * speed))

    def scroll_free(self, dx: float, dy: float) -> None:
        """Direct pixel scroll (no accumulation). For smooth-scroll contexts."""
        hbar = self._view.horizontalScrollBar()
        vbar = self._view.verticalScrollBar()
        hbar.setValue(int(hbar.value() + dx))
        vbar.setValue(int(vbar.value() + dy))

    def zoom(self, delta: float) -> None:
        """Analog zoom. Positive = in, negative = out."""
        factor = 1.0 + delta * 0.015
        projected = self._view.transform().m11() * factor
        from .canvas_view import CanvasView
        if CanvasView.MIN_SCALE < projected < CanvasView.MAX_SCALE:
            self._view.scale(factor, factor)


# ═══════════════════════════════════════════════════════════
# JoystickNavigator — reads USB joystick, feeds ViewNavigator
# ═══════════════════════════════════════════════════════════

class JoystickNavigator(QObject):
    """Polls a USB joystick at ~60 fps. Feeds the ViewNavigator.

    Dead zone = D-mapped: the threshold to push past before a cell step
    registers. Below the dead zone = sub-cell, ignored. Past it = committed
    to at least 1 cell of movement.
    """

    def __init__(self, canvas_view, navigator: ViewNavigator,
                 joy_id: int = 0, parent=None) -> None:
        super().__init__(parent or canvas_view)
        self._view = canvas_view
        self._nav = navigator
        self._joy_id = joy_id
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._dead_zone = 0.12
        self._zoom_dead_zone = 0.15
        self._active = False
        self._connected = False

    def start(self) -> None:
        self._active = True
        self._connected = joystick_available(self._joy_id)
        self._timer.start(16)

    def stop(self) -> None:
        self._active = False
        self._timer.stop()

    @property
    def connected(self) -> bool:
        return self._connected

    def _poll(self) -> None:
        if not self._active:
            return
        win = self._view.window()
        if win is None or not win.isActiveWindow():
            return
        info = _read_joy(self._joy_id)
        if info is None:
            if self._connected:
                self._connected = False
            return
        if not self._connected:
            self._connected = True

        dz = self._dead_zone
        x = (info.dwXpos - _MID) / _MID
        y = (info.dwYpos - _MID) / _MID
        if abs(x) < dz:
            x = 0.0
        if abs(y) < dz:
            y = 0.0

        self._nav.push(x, y)

        z = (info.dwZpos - _MID) / _MID
        if abs(z) > self._zoom_dead_zone:
            self._nav.zoom(z)
