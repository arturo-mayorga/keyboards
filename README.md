# keyboards

Two split keyboards, deliberately kept in sync so muscle memory transfers
between them.

| Board | Firmware | Config |
|---|---|---|
| Corne (CorneKBH, wireless) | ZMK | [`zmk-config-cornekbh/`](https://github.com/arturo-mayorga/zmk-config-cornekbh) |
| Moonlander Mark I rev B | QMK (ZSA fork) | [`zsa-config-monnlander/`](https://github.com/arturo-mayorga/zsa-config-monnlander) |

Each board's configuration lives in its own repo. This repo tracks both as
submodules, so a commit here names the exact **pair** of configurations that
were in sync at that moment — which is what makes parity checkable after the
fact rather than merely intended.

## Why

Two keyboards with different layouts means two sets of habits, and every switch
between them costs a re-adjustment. So rather than let each board drift toward
whatever its configurator makes easy, both implement one shared layout.

The Corne is the reference. The Moonlander mirrors it. Where the Moonlander has
keys the Corne lacks — its number row, inner columns, bottom row — those keys
carry extra functions, but never ones that contradict a Corne binding.

## Clone

Submodules, so:

```sh
git clone --recurse-submodules https://github.com/arturo-mayorga/keyboards.git
```

Already cloned without them:

```sh
git submodule update --init --recursive
```

## The shared layout

Full contract in [`layout/SPEC.md`](layout/SPEC.md). In brief:

**Base layer is alphas only.** Numbers, symbols and navigation live on layers
reached by holding a thumb key. Layer access is momentary everywhere — no
toggles.

| # | Layer | Held with |
|---|---|---|
| 0 | Base | — |
| 1 | NavNum | Space (right thumb) |
| 2 | Symbols | left thumb |
| 3 | System | layers 1 + 2 together |
| 4 | Extra (mouse) | right pinky |

**Home-row mods are minimal**: only `A` and `;` hold for Shift. Ctrl, GUI and
Alt get dedicated keys.

**Symbols come mostly from combos** — 17 two-key rolls, nearly all vertical
finger pairs on the same column:

| | | | |
|---|---|---|---|
| W+S `@` | E+D `#` | R+F `$` | T+G `%` |
| F+V `=` | S+X `\` | A+B `Esc` | D+L `Del` |
| U+J `+` | I+K `*` | H+N `_` | J+M `−` |
| K+, `/` | M+, `[` | ,+. `]` | |
| J+K `(` → `<` | K+L `)` → `>` | | |

**Layer feedback differs by necessity.** The Corne shows the active layer on its
nice!view screen; the Moonlander has no screen, so it lights the whole board a
distinct colour per layer — white, green, blue, red, yellow for layers 0–4.

Differences that are deliberate are recorded in
[`layout/divergences.md`](layout/divergences.md). Anything else that differs
between the two configs is a bug.

## Working on a layout

Change the Corne first, mirror to the Moonlander, then commit each submodule
and the pointer bump here. Details, plus a ZMK→QMK translation table, in the
`keyboard-parity` skill.

### Moonlander

From `zsa-config-monnlander/`:

```sh
make build      # compile, if the keymap changed since last time
make flash      # build if needed, then flash the attached board
```

Then press the physical reset button when prompted. `make help` reports what it
would do and for which revision.

The Mark I ships as rev A and rev B. They look identical, share a model name,
and take firmware linked at different addresses — an image written at the wrong
one will not boot. So the Makefile reads the revision off the attached board's
USB id rather than assuming (`tools/detect-revision.sh` in that repo, which
recognises both the normal-mode and the bootloader-mode ids, since you may run
`make flash` either side of pressing reset). `REV=reva` or `REV=revb` overrides
it; with no board attached, builds fall back to rev B.

Two things that are easy to lose a morning to:

- **`wally-cli` cannot flash this board.** It expects the older STM32 DFU id
  `0483:df11`; this Moonlander has ZSA's ignition bootloader, `3297:2003`, and
  wally bails out before writing. `make flash` goes through `qmk flash`, which
  takes the DFU arguments from the board definition and so cannot get the
  address wrong.
- **GCC 16 breaks QMK's bootloader-jump assembly.** `tools/patches/` has the
  one-line constraint fix. It applies to the QMK clone, not to this repo, so a
  `git pull` there silently reverts it and builds start failing again. The
  Makefile does not guard against this — the build simply fails again.

The build runs out of a QMK tree that the keymap directory is symlinked into;
`make` says how to create that link if it is missing. First-time toolchain
setup: [`tools/setup-toolchain.sh`](tools/setup-toolchain.sh).

### Corne

Firmware builds in GitHub Actions from `build.yaml`; copy the resulting `.uf2`
to each half in bootloader mode. Small keymap edits can go through ZMK Studio
over USB instead. `scripts/keymap_cheatsheet.py` regenerates
[the visual keymap](zmk-config-cornekbh/docs/keymap.html) from the keymap source,
so the docs cannot drift from the firmware.

## Tools

```sh
python3 tools/check-parity.py            # do the two boards still agree?
python3 tools/moonlander-cheatsheet.py   # regenerate the Moonlander diagrams
```

`check-parity.py` parses both keymaps and compares combos, tap-hold timings and
layer count, so parity is verified rather than assumed. Run it before
committing a layout change.

Visual keymaps: [Moonlander](docs/moonlander/keymap.html) ·
[Corne](zmk-config-cornekbh/docs/keymap.html). Both are generated from their
keymap sources and should be regenerated after any change.

## Layout

```
CLAUDE.md              context for Claude Code, scoped to this directory
.claude/skills/        board procedures — parity, moonlander, corne
layout/SPEC.md         the normative shared contract
layout/divergences.md  intentional differences
tools/                 parity check, diagram generator, toolchain setup, patches
docs/                  reference images
```
