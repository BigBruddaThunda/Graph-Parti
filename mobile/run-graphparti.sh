#!/data/data/com.termux/files/usr/bin/bash
# ───────────────────────────────────────────────────────────────────────────
# GRAPH PARTI · launcher (Termux side) — what `gp` runs.
#
#   Starts the Termux:X11 server, then logs into Debian and launches the app
#   on that display. Stylus events flow straight through X11 to Qt.
#
#   Usage:
#     gp                 # split-pane cockpit  (python main.py)
#     gp canvas          # canvas only         (python -m graphparti)
#     gp -- <anything>   # run an arbitrary command inside the Debian venv
# ───────────────────────────────────────────────────────────────────────────
set -euo pipefail

DISTRO="${GP_DISTRO:-debian}"
DISPLAY_NUM="${GP_DISPLAY:-:0}"
REPO_DIR="${GP_REPO_DIR:-/root/Graph-Parti}"
VENV="${GP_VENV:-$REPO_DIR/.venv}"

say()  { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }

# --- pick what to run inside Debian ----------------------------------------
MODE="${1:-cockpit}"
case "$MODE" in
  canvas)  INNER="cd '$REPO_DIR' && '$VENV/bin/python' -m graphparti" ;;
  cockpit) INNER="cd '$REPO_DIR' && '$VENV/bin/python' main.py" ;;
  --)      shift; INNER="cd '$REPO_DIR' && '$VENV/bin/python' $*" ;;
  *)       INNER="cd '$REPO_DIR' && '$VENV/bin/python' main.py" ;;
esac

# --- start the X11 server (idempotent) -------------------------------------
say "Starting Termux:X11 on $DISPLAY_NUM …"
pkill -f "termux-x11 $DISPLAY_NUM" 2>/dev/null || true
# Launch the Android-side activity if available (brings the X11 window forward)
am start -n com.termux.x11/.MainActivity >/dev/null 2>&1 || \
  warn "Couldn't auto-open the Termux:X11 app — open it from your home screen, then re-run gp."
termux-x11 "$DISPLAY_NUM" >/dev/null 2>&1 &
X11_PID=$!
sleep 2

# --- optional audio (harmless if unused) -----------------------------------
pulseaudio --start --exit-idle-time=-1 2>/dev/null || true

# --- boot Debian and run the app on that display ---------------------------
say "Launching GRAPH PARTI ($MODE)…"
proot-distro login "$DISTRO" --shared-tmp -- bash -lc "
  export DISPLAY=$DISPLAY_NUM
  export QT_QPA_PLATFORM=xcb
  export QT_AUTO_SCREEN_SCALE_FACTOR=1   # HiDPI phone screens
  export PULSE_SERVER=127.0.0.1
  $INNER
"

# --- tidy up the X server when the app exits -------------------------------
kill "$X11_PID" 2>/dev/null || true
say "GRAPH PARTI exited."
