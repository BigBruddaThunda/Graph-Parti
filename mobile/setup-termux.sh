#!/data/data/com.termux/files/usr/bin/bash
# ───────────────────────────────────────────────────────────────────────────
# GRAPH PARTI · Stage 1 — Termux side (run this FIRST, inside the Termux app)
#
#   Installs proot + a glibc Debian Trixie rootfs, then drops you a launcher
#   (`gp`) that enters Debian and continues with Stage 2 automatically.
#
#   Run:   bash setup-termux.sh
#   (or, fresh phone:  pkg install -y git && git clone <repo> && cd Graph-Parti/mobile && bash setup-termux.sh)
# ───────────────────────────────────────────────────────────────────────────
set -euo pipefail

say()  { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# --- sanity: are we actually in Termux? -----------------------------------
[ -n "${PREFIX:-}" ] && [ -d "$PREFIX" ] || die "This must be run inside the Termux app (PREFIX not set)."
case "$(uname -m)" in
  aarch64|arm64) ok "arch $(uname -m) — good, PySide6 ships an aarch64 wheel." ;;
  *) warn "arch $(uname -m) is unusual for a phone; PySide6 aarch64 wheel may not match." ;;
esac

DISTRO="${GP_DISTRO:-debian}"   # proot-distro alias; debian = Trixie (glibc 2.41 ≥ 2.39 required)

say "Updating Termux packages…"
yes | pkg upgrade -y >/dev/null 2>&1 || pkg upgrade -y || true

say "Installing Termux deps (proot-distro, git, x11-repo, termux-x11 helpers)…"
pkg install -y proot-distro git x11-repo >/dev/null
# pulse + x11 helpers live in x11-repo; ignore if a given package name drifts
pkg install -y termux-x11-nightly pulseaudio 2>/dev/null || \
  warn "Couldn't auto-install termux-x11-nightly via pkg — you'll install the Termux:X11 APK manually (see README)."

say "Installing the Debian Trixie rootfs via proot-distro (this is the big download)…"
if proot-distro list 2>/dev/null | grep -q "^${DISTRO}.*installed"; then
  ok "Debian rootfs already installed — skipping."
else
  proot-distro install "$DISTRO"
fi

# --- copy Stage 2 into the rootfs so it survives the proot boundary --------
ROOTFS="$PREFIX/var/lib/proot-distro/installed-rootfs/$DISTRO"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SELF_DIR/setup-debian.sh" ]; then
  install -Dm755 "$SELF_DIR/setup-debian.sh" "$ROOTFS/root/setup-debian.sh"
  ok "Staged setup-debian.sh into the Debian rootfs (/root/setup-debian.sh)."
else
  warn "setup-debian.sh not found next to this script — fetch it from the repo's mobile/ folder."
fi

# --- install the `gp` launcher into Termux's PATH --------------------------
LAUNCHER="$PREFIX/bin/gp"
cat > "$LAUNCHER" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
# GRAPH PARTI launcher — boots Debian, starts X11, runs the cockpit.
exec bash "$SELF_DIR/run-graphparti.sh" "\$@"
EOF
chmod +x "$LAUNCHER"
ok "Installed launcher: type 'gp' anytime to start GRAPH PARTI."

echo
ok "Stage 1 complete."
cat <<EOF

Next:
  1) Finish the Debian side — enter Debian and run Stage 2:
         proot-distro login $DISTRO -- bash /root/setup-debian.sh
     (installs Python 3.13 + PySide6 + clones the repo inside Debian)

  2) Then just run:  gp
     …which starts Termux:X11 and launches the split-pane cockpit.

If 'termux-x11' didn't install above, install the Termux:X11 APK from
https://github.com/termux/termux-x11/releases  (see ../mobile/README.md).
EOF
