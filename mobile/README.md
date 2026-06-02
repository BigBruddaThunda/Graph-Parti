# 📱 GRAPH PARTI on Android — Termux setup

Run the **real** GRAPH PARTI + Archideck cockpit on your phone, with a stylus —
no rewrite, no cross-compile. This runs the same `python main.py` you'd run on a
PC, inside a glibc Linux on your phone, drawn to the screen by Termux:X11.

> **Why not a real `.apk`?** PySide6/Qt6 *can* be packaged to Android
> (`pyside6-android-deploy`), but it needs an **x86 Linux host + Android NDK to
> build** (you can't build it from the phone), and it's experimental. The Termux
> route below runs the unmodified code today and handles a stylus well. When we
> later want a true installable `.apk`, that's a separate desktop-build task —
> see [the dead-end note](#about-a-true-apk-later) at the bottom.

---

## What you'll install (all free, all from F-Droid / GitHub)

| App | Where | Why |
|-----|-------|-----|
| **Termux** | [F-Droid](https://f-droid.org/packages/com.termux/) | the Linux terminal. **Do NOT use the Play Store build — it's abandoned.** |
| **Termux:X11** | [GitHub releases](https://github.com/termux/termux-x11/releases) | the display server that draws Qt windows (stylus passthrough). |
| *(optional)* **Termux:Widget** | [F-Droid](https://f-droid.org/packages/com.termux.widget/) | a home-screen button that launches GRAPH PARTI like an app. |

Install Termux + Termux:X11 first, open Termux once so it finishes setup, then:

---

## The 4 commands (copy-paste in order)

```bash
# 1) get git + this repo (it's PUBLIC, so no login needed)
pkg install -y git
git clone https://github.com/BigBruddaThunda/Graph-Parti.git
cd Graph-Parti/mobile

# 2) Stage 1 — Termux side: proot + Debian Trixie + the `gp` launcher
bash setup-termux.sh

# 3) Stage 2 — Debian side: Python 3.13 + PySide6 + venv (big download, ~once)
proot-distro login debian -- bash /root/setup-debian.sh

# 4) launch it
gp
```

That's it. `gp` opens the split-pane cockpit. After this, **launching is just
`gp`** any time you open Termux.

### Modes

```bash
gp            # split-pane: canvas + Archideck cockpit  (python main.py)
gp canvas     # canvas only                              (python -m graphparti)
gp -- main.py --whatever   # run anything inside the Debian venv
```

---

## ⚠️ The one trap that will waste your afternoon: glibc

The PySide6 ARM wheel is built for **`manylinux_2_39` → glibc ≥ 2.39**.

- **Debian Trixie** (what `proot-distro install debian` gives you now) → glibc 2.41 ✅
- **Debian Bookworm (12)** → glibc 2.36 ❌ `pip install PySide6` fails at the end
- **Ubuntu 24.04 (Noble)** → glibc 2.39 ✅ (alternative: `GP_DISTRO=ubuntu`)

`setup-debian.sh` **checks this and refuses early** with a clear message instead
of letting pip fail cryptically. If it stops you, do:

```bash
proot-distro remove debian && proot-distro install debian   # reinstalls Trixie
```

---

## Stylus / drawing notes

- Termux:X11 forwards touch + stylus as X pointer events, so the canvas's
  snap (grid + endpoints/midpoints), line/rect/circle/polyline tools, and
  select/move all respond to the pen.
- In the Termux:X11 app **preferences**, turn on **"Stylus/pen mode"** (and
  *touchscreen as mouse* if your pen taps don't register). HiDPI is handled —
  `QT_AUTO_SCREEN_SCALE_FACTOR=1` is set by the launcher.
- Pressure-sensitive *painting* (the future raster layer) depends on X11
  exposing pressure; basic vector drafting works regardless.

---

## Home-screen launcher (optional, makes it feel like an app)

With **Termux:Widget** installed:

```bash
mkdir -p ~/.shortcuts
ln -sf "$PREFIX/bin/gp" ~/.shortcuts/GRAPH-PARTI
```

Then add the **Termux:Widget** widget to your home screen and tap
**GRAPH-PARTI**. One tap → cockpit.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Black screen / "cannot connect to display" | Open the **Termux:X11 app** first, then run `gp`. The X server lives in that app. |
| `qt.qpa.plugin: could not load the Qt platform plugin "xcb"` | A runtime lib is missing — re-run `setup-debian.sh` (it installs the `libxcb-*` set). |
| `pip` ends with `No matching distribution for PySide6` | glibc too old → reinstall Trixie (see the glibc trap above). |
| App is tiny / huge | Adjust Termux:X11 **display scale**, or set `QT_SCALE_FACTOR=1.5` before `gp`. |
| Want to update the code | `proot-distro login debian -- bash -lc 'cd ~/Graph-Parti && git pull'` |

---

## How the pieces fit

```
┌─ Termux (Android app) ───────────────────────────────────────┐
│  setup-termux.sh   → proot-distro + Debian rootfs + `gp`      │
│  run-graphparti.sh → starts Termux:X11, then…                 │
│      proot-distro login debian ──────────────────────────────┼─┐
│                                                               │ │
└───────────────────────────────────────────────────────────────┘ │
   ┌─ Debian Trixie (proot, glibc 2.41) ◄───────────────────────────┘
   │  setup-debian.sh → Python 3.13 + venv + PySide6 + clone repo
   │  python main.py  → CanvasWidget + ArchideckPanel (split-pane)
   │        │ draws via DISPLAY=:0 ─────────────────────────────┐
   └────────┼──────────────────────────────────────────────────┘
            ▼
   Termux:X11 window  ← your stylus draws here
```

The repo is self-contained: `graphparti/` (the isolated canvas) **and**
`archideck/` (the cockpit that embeds it) both live here, so the phone clones
**one public repo** and gets the whole instrument.

---

## About a true `.apk` (later)

When we want a tap-to-install `.apk` (no Termux), the path is **not** from the
phone. It's a desktop build:

1. x86-64 **Linux** host + **Android NDK r26/r27** + the matching
   `Qt for Android` (aarch64) install.
2. `pip install pyside6-android-deploy` then
   `pyside6-android-deploy --name GraphParti --wheel-pyside <...> --wheel-shiboken <...>`.
3. Qt's Android support has **no QGraphicsView quirks per se**, but the cockpit's
   desktop window-splitter UX would want a mobile re-layout first (the
   "mobile UI/interface" track in the pickup note).

So the staged plan is: **(now)** Termux to build/test features with the stylus →
**(when stable)** invest in the NDK build for a standalone `.apk`. This folder is
step one.
