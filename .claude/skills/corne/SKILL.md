---
name: corne
description: Work on the CorneKBH ZMK config — keymap edits, combos, builds, and flashing. Use when changing corne.keymap, adding combos or behaviors, or regenerating the keymap cheat sheet. Triggers: corne, zmk, keymap.corne, zmk studio, nice_nano.
---

# Corne (CorneKBH)

Wireless Corne on `nice_nano_v2` with nice!view displays. ZMK. This board is the
**reference implementation** of the shared layout — see `layout/SPEC.md`.

## Layout

`config/corne.keymap`, 42 keys: 3 rows × 12 (both halves) then 6 thumbs.
Position numbering runs left to right, top to bottom:

| Range | Row |
|---|---|
| 0–11 | top |
| 12–23 | home |
| 24–35 | bottom |
| 36–41 | thumbs (36 leftmost … 41 rightmost) |

Combos are declared by **key position**, so any change to the physical layout
invalidates them. The QMK side declares the same combos by *keycode* — see
`layout/SPEC.md` for the mapping and why that difference matters.

## Building

Firmware builds in GitHub Actions from `build.yaml`; download the artifacts and
copy the `.uf2` to each half in bootloader mode. There is no local build here,
so there is no `make build`/`make flash` as on the Moonlander — the asymmetry
is the remote build, not an oversight.

For quick keymap edits without a firmware build, ZMK Studio works over USB —
see the repo README. Studio is enabled via `CONFIG_ZMK_STUDIO=y` and unlocked
with `&studio_unlock` on the System layer.

## Cheat sheet

`scripts/keymap_cheatsheet.py` parses `corne.keymap` directly and regenerates
`docs/keymap.html` plus per-layer SVGs. Deterministic — rerun after any keymap
change so the docs cannot drift from the firmware.

```
python3 scripts/keymap_cheatsheet.py
```
