#!/usr/bin/env bash
#
# Install the toolchain needed to build ZSA Moonlander firmware from source
# on Arch Linux, and set up device access for flashing.
#
# Review before running:  bash setup-toolchain.sh
# Everything here is idempotent — safe to re-run.
#
set -euo pipefail

# ---------------------------------------------------------------------------
# What gets installed, and why
# ---------------------------------------------------------------------------
#   qmk                     QMK CLI: `qmk compile`, `qmk flash`
#   arm-none-eabi-gcc       C compiler for the Moonlander's STM32 (ARM) MCU
#   arm-none-eabi-newlib    C library for that target; linking fails without it
#   arm-none-eabi-binutils  assembler/linker/objcopy for the same target
#   dfu-util                low-level USB DFU flasher (fallback / debugging)
#   zsa-wally-cli           ZSA's flasher — the normal way to flash a Moonlander
#   zsa-udev                udev rules so flashing works as your user, not root
#
PACKAGES=(
  qmk
  arm-none-eabi-gcc
  arm-none-eabi-newlib
  arm-none-eabi-binutils
  dfu-util
  zsa-wally-cli
  zsa-udev
)

# ---------------------------------------------------------------------------
# Preflight: the package databases have to match the mirror
# ---------------------------------------------------------------------------
# Omarchy's mirror is a rolling snapshot. When the local sync databases fall
# behind it, pacman asks for package versions the mirror no longer carries and
# dies partway through the download with a 404, e.g.
#
#   error: failed retrieving file 'avr-libc-2.3.2-1-any.pkg.tar.zst'
#          from stable-mirror.omarchy.org : The requested URL returned error: 404
#
# The fix is a full system update (`omarchy update`), which refreshes the
# databases and snapshots the system first. This script deliberately does NOT
# run it for you: a system-wide upgrade is a much bigger action than installing
# a keyboard toolchain, and it should be your call, not a side effect.
#
# A bare `pacman -Sy` is NOT the fix — it would refresh the databases without
# upgrading installed packages, leaving a partial-upgrade state that Arch does
# not support.
#
# Note on what is NOT checked here: the age of /var/lib/pacman/sync/*.db is a
# useless signal on Omarchy. The stable mirror is a dated snapshot, so those
# files legitimately read as days old even immediately after a successful
# update. Only the actual URLs tell the truth, so ask the mirror directly.
echo "==> Checking that every package is actually fetchable"
urls=$(pacman -Sp --needed "${PACKAGES[@]}" 2>/dev/null) || {
  echo "Could not resolve the package list. Are the repos configured?" >&2
  exit 1
}
missing=""
for u in $urls; do
  case "$u" in
    file://*)
      # Already in the local pacman cache; pacman uses it without downloading.
      [ -f "${u#file://}" ] || missing="$missing $u"
      ;;
    *)
      code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -I "$u" || echo 000)
      [ "$code" = "200" ] || missing="$missing $u ($code)"
      ;;
  esac
done

if [ -n "$missing" ]; then
  echo
  echo "The mirror cannot serve these files:"
  for m in $missing; do echo "    $m"; done
  echo
  echo "This means the local package databases disagree with the mirror."
  echo "Run a system update, then re-run this script:"
  echo
  echo "    omarchy update"
  echo
  exit 1
fi
echo "    all $(echo "$urls" | grep -c .) packages reachable"

echo "==> Installing packages (all from the 'extra' repo, no AUR)"
sudo pacman -S --needed "${PACKAGES[@]}"

# ---------------------------------------------------------------------------
# Device access
# ---------------------------------------------------------------------------
# zsa-udev drops rules in /usr/lib/udev/rules.d that grant your user write
# access to the keyboard while it sits in bootloader mode. Reload so they
# apply without a reboot. The keyboard must be UNPLUGGED and REPLUGGED after
# this for the new rules to take effect on the device node.
echo
echo "==> Reloading udev rules"
sudo udevadm control --reload-rules
sudo udevadm trigger

# ZSA's rules gate on the 'plugdev' group on some systems. Arch's zsa-udev
# package uses uaccess (no group needed), so this is a no-op safety net that
# only acts if a plugdev group actually exists on this machine.
if getent group plugdev >/dev/null 2>&1; then
  if ! id -nG "$USER" | grep -qw plugdev; then
    echo "==> Adding $USER to the 'plugdev' group (log out/in to take effect)"
    sudo usermod -aG plugdev "$USER"
  fi
fi

# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
echo
echo "==> Verifying installed tools"
status=0
for cmd in qmk arm-none-eabi-gcc dfu-util wally-cli; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf '    %-20s %s\n' "$cmd" "$(command -v "$cmd")"
  else
    printf '    %-20s MISSING\n' "$cmd"
    status=1
  fi
done

echo
if [ "$status" -eq 0 ]; then
  echo "All tools present. Next: unplug and replug the Moonlander, then tell"
  echo "Claude to run the baseline build."
else
  echo "Something did not install. Re-run this script or check the pacman output above."
fi
exit "$status"
