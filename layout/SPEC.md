# Shared layout contract

Normative. Both boards implement this. The Corne (`config/corne.keymap`) is the
reference; the Moonlander (`zsa_moonlander_layout_source/keymap.c`) mirrors it.

## Layers

| # | Name | Access | Contents |
|---|---|---|---|
| 0 | Base | — | alphas only (Moonlander additionally keeps its number row) |
| 1 | NavNum | momentary, right thumb on Space | 1–0 on the top alpha row; numpad on right home block; arrows on X/C/V with Up on D |
| 2 | Symbols | momentary, left thumb | `!@#$%` `^&*()`, brackets, braces, pipe |
| 3 | System | **tri-layer**: hold 1 + 2 | F1–F12, bootloader, radio/RGB controls |
| 4 | Extra | `MO(4)`, right pinky bottom row | mouse move, click, scroll |

Layer access is **momentary everywhere**. No toggles.

## Home-row mods

Only two, both Shift:

| Key | Tap | Hold |
|---|---|---|
| `A` | a | Left Shift |
| `;` | ; | Right Shift |

`Z`, `X` and `/` are plain letters. Ctrl / GUI / Alt live on dedicated keys.

## Tap-hold timings

| ZMK (`hm` behavior) | QMK | Value |
|---|---|---|
| `tapping-term-ms` | `TAPPING_TERM` | 200 |
| `quick-tap-ms` | `QUICK_TAP_TERM` | 180 |
| `require-prior-idle-ms` | `FLOW_TAP_TERM` | 120 |

ZMK flavor is `tap-preferred`. On the QMK side this means `PERMISSIVE_HOLD` and
`HOLD_ON_OTHER_KEY_PRESS` must stay **undefined** — defining either makes the
Moonlander resolve holds differently from the Corne.

## Combos

Combo term 50 ms on both (ZMK default; `COMBO_TERM` on QMK). All are two-key.

| Pair | Output | | Pair | Output |
|---|---|---|---|---|
| W + S | `@` | | U + J | `+` |
| E + D | `#` | | I + K | `*` |
| R + F | `$` | | H + N | `_` |
| T + G | `%` | | J + M | `−` |
| F + V | `=` | | K + `,` | `/` |
| S + X | `\` | | M + `,` | `[` |
| A + B | `Esc` | | `,` + `.` | `]` |
| D + L | `Del` | | J + K | `(` → `<` shifted |
| | | | K + L | `)` → `>` shifted |

`Esc` and `Del` fire on every layer. Every other combo is base-layer only.

ZMK matches combos by key position, QMK by keycode — so the QMK side must spell
`A` as its mod-tap keycode, `MT(MOD_LSFT, KC_A)`, or that combo silently never
fires.

## Thumbs

| Role | Corne | Moonlander |
|---|---|---|
| GUI | left thumb, outer | key formerly Backspace |
| Symbols layer | left thumb, middle | key formerly `TO(1)` |
| Alt | left thumb, inner | key formerly Delete |
| Return | right thumb, inner | Enter — unchanged |
| Space / NavNum | right thumb, middle | Space — tap types space, hold is NavNum |
| End | right thumb, outer | key formerly Left arrow |

Enter and Space keep their tap behavior on both boards; those two were the most
ingrained and were deliberately left alone.

## Layer feedback

The Corne reports the active layer on its nice!view screen. The Moonlander has
no screen, so it signals the same information with a distinct solid RGB colour:

| Layer | Colour |
|---|---|
| Base | white |
| NavNum | green |
| Symbols | blue |
| System | red |
| Extra | yellow |
