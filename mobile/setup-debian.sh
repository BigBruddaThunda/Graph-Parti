#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────────────────
# GRAPH PARTI · Stage 2 — Debian side (runs INSIDE proot Debian)
#
#   Verifies glibc ≥ 2.39 (PySide6 aarch64 wheel hard requirement), installs
#   Python 3.13 + a venv with PySide6, clones the Graph-Parti repo, and leaves
#   everything ready for `gp`.
#
#   Run (from Termux):  proot-distro login debian -- bash /root/setup-debian.sh
# ───────────────────────────────────────────────────────────────────────────
set -euo pipefail

say()  { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

REPO_URL="${GP_REPO_URL:-https://github.com/BigBruddaThunda/Graph-Parti.git}"
REPO_DIR="${GP_REPO_DIR:-/root/Graph-Parti}"
BRANCH="${GP_BRANCH:-master}"
VENV="${GP_VENV:-$REPO_DIR/.venv}"

# --- glibc gate: the wheel needs manylinux_2_39 (glibc ≥ 2.39) -------------
GLIBC="$(ldd --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+' | head -1 || echo 0)"
say "Detected glibc $GLIBC (PySide6 aarch64 wheel needs ≥ 2.39)."
awk "BEGIN{exit !($GLIBC >= 2.39)}" || die \
"glibc $GLIBC is too old for the PySide6 wheel.
 You're likely on Debian Bookworm (12). Reinstall with Trixie:
     proot-distro remove debian && proot-distro install debian
 (proot-distro's 'debian' alias now points at Trixie / glibc 2.41.)
 Ubuntu 24.04 (Noble, glibc 2.39) also works."

say "Updating apt + installing build/runtime deps…"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null
# python3 (Trixie ships 3.13), venv, pip, git, and the X/GL/font libs Qt loads at runtime
apt-get install -y --no-install-recommends \
  python3 python3-venv python3-pip git \
  libgl1 libegl1 libxkbcommon0 libxkbcommon-x11-0 libdbus-1-3 \
  libfontconfig1 libfreetype6 fontconfig \
  libx11-xcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
  libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xfixes0 \
  >/dev/null
ok "System deps installed."

PYBIN="$(command -v python3)"
PYVER="$("$PYBIN" -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
say "Using $PYBIN (Python $PYVER)."
awk "BEGIN{exit !($PYVER >= 3.10)}" || die "Need Python ≥ 3.10 (PySide6 floor). Got $PYVER."

# --- clone / update the repo ----------------------------------------------
if [ -d "$REPO_DIR/.git" ]; then
  say "Repo present — fetching latest…"
  git -C "$REPO_DIR" fetch --depth 1 origin "$BRANCH" && \
  git -C "$REPO_DIR" checkout "$BRANCH" && \
  git -C "$REPO_DIR" pull --ff-only origin "$BRANCH" || warn "git update skipped (offline?)."
else
  say "Cloning $REPO_URL …"
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi
ok "Repo at $REPO_DIR"

# --- venv + PySide6 --------------------------------------------------------
say "Creating venv at $VENV …"
"$PYBIN" -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install --upgrade pip >/dev/null
say "Installing PySide6 (large download — the aarch64 wheel)…"
pip install -r "$REPO_DIR/requirements.txt"
ok "PySide6 installed."

# --- smoke test: can we import Qt + the canvas package? --------------------
say "Smoke-testing imports (no display needed)…"
QT_QPA_PLATFORM=offscreen python - <<PY
import PySide6, importlib
from PySide6 import QtWidgets  # loads the Qt libs
app = QtWidgets.QApplication([])
import graphparti  # the canvas package
print("PySide6", PySide6.__version__, "· graphparti", graphparti.__version__, "OK")
PY
ok "Imports work."

echo
ok "Stage 2 complete. Back in Termux, run:  gp"
