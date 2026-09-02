---
name: keyboard-parity
description: Keep the Corne and Moonlander layouts synchronized so muscle memory transfers. Use when changing a layout on either board, porting a ZMK behavior to QMK (or back), or checking whether the two configs still agree. Triggers: parity, sync keyboards, port combo, both keyboards, layout change.
---

# Keeping the two boards in sync

`layout/SPEC.md` is the contract. The Corne is the reference; the Moonlander
mirrors it. A change to one board is not done until the other matches or the
difference is recorded in `layout/divergences.md`.

## Procedure for a layout change

1. Change the Corne first (`config/corne.keymap`), since it is the reference.
2. Regenerate its cheat sheet: `python3 scripts/keymap_cheatsheet.py`.
3. Mirror into `zsa-config-monnlander/zsa_moonlander_layout_source/keymap.c`.
4. Update `layout/SPEC.md` if the contract itself changed.
5. Build and flash the Moonlander (see the `moonlander` skill).
6. Commit each submodule, then commit the pointer bump here — that parent
   commit is what records the two configs as a matched pair.

## ZMK → QMK translation

| ZMK | QMK |
|---|---|
| `&mo N` / `&lt N KEY` | `MO(N)` / `LT(N, KEY)` |
| `&kp X` | `KC_X` |
| hold-tap `&hm MOD KEY` | `MT(MOD_x, KC_KEY)` |
| `tapping-term-ms` | `TAPPING_TERM` |
| `quick-tap-ms` | `QUICK_TAP_TERM` |
| `require-prior-idle-ms` | `FLOW_TAP_TERM` |
| flavor `tap-preferred` | QMK default — leave `PERMISSIVE_HOLD` and `HOLD_ON_OTHER_KEY_PRESS` undefined |
| `zmk,combos` | `COMBO_ENABLE` + `combo_t key_combos[]` |
| combo `layers = <0>` | `combo_should_trigger()` |
| `zmk,behavior-mod-morph` | `process_record_user()` (a key override cannot swap `KC_LPRN`, which is itself Shift+9) |
| `zmk,behavior-caps-word` | `CAPS_WORD_ENABLE`, `CW_TOGG` |
| `zmk,behavior-tap-dance` | `TAP_DANCE_ENABLE` |
| `conditional_layers` | `update_tri_layer_state()` in `layer_state_set_user` |
| `&bt`, `&studio_unlock` | no equivalent — wired board, use RGB / `QK_BOOT` |
| `&mmv`, `&mkp`, `&msc` | `MOUSEKEY_ENABLE`, `KC_MS_*` |
| macro pressing Ctrl+Tab | just `LCTL(KC_TAB)` — no macro needed |

## Traps

- **Combos and mod-taps.** QMK matches combos on the keycode as written in the
  keymap. `A` is `MT(MOD_LSFT, KC_A)`, not `KC_A`. A combo referencing `KC_A`
  compiles fine and silently never fires.
- **Combo identity differs.** ZMK combos are positional, QMK's are by keycode.
  This is why they survive the move to a different physical grid — but it also
  means a QMK combo follows the letter wherever it goes.
- **The Moonlander needs a revision.** `-kb zsa/moonlander` fails; use
  `zsa/moonlander/revb`.
- **Do not blindly copy layer numbers from an Oryx export.** Oryx generates
  `TO()` toggles; this layout is momentary throughout.

## Physical mapping

The Corne's 3×5 alpha core sits on the Moonlander's rows 2–4:

| Corne row | Moonlander row | Left outer | Right outer |
|---|---|---|---|
| 1 (Q W E R T) | 2 | Tab | Backspace (was Enter) |
| 2 (A S D F G) | 3 | LShift (was Caps) | `'` |
| 3 (Z X C V B) | 4 | LCtrl (was LShift) | `MO(4)` (was `\`) |

Moonlander keys with no Corne counterpart keep their own functions — see
`layout/divergences.md`.
