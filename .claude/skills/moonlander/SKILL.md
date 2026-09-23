---
name: moonlander
description: Build and flash firmware for the ZSA Moonlander Mark I rev B from source. Use when compiling the QMK keymap, flashing the board, recovering from a bad flash, or setting up the toolchain. Triggers: moonlander, make build, make flash, qmk compile, dfu-util, wally, flash keyboard, bootloader.
---

# Moonlander: build and flash

**Identify the revision before doing anything.** These boards look identical,
share a model name, and take incompatible firmware. Read the USB id first:

| Normal-mode id | Bootloader-mode id | Revision | Build target |
|---|---|---|---|
| `3297:1969` | `0483:df11` | rev A | `zsa/moonlander/reva` |
| `3297:1972` | `3297:2003` | rev B | `zsa/moonlander/revb` |

`make` does this for itself, so the targets below never have to be told which
revision to use. To ask directly:

```sh
zsa-config-monnlander/tools/detect-revision.sh   # reva | revb | none | ambiguous
```

It encodes the table above, both columns, because the board answers to a
different id once reset has been pressed and it may be called either side of
that. `0483:df11` is ST's generic DFU id rather than a ZSA one, so it only
counts as a rev A Moonlander when no `3297` device is present at all.

The two revisions differ in real hardware, not just a flag:

| | rev A | rev B |
|---|---|---|
| Settings storage | 24LC128 EEPROM chip on I2C | emulated in MCU flash (wear levelling) |
| Bootloader | STM32 ROM DFU, `0483:df11` | ZSA "ignition", `3297:2003`, occupying the first 8 KB |
| Link address | `0x08000000` | `0x08002000` |

Both use the same MCU, the same MCP23018 matrix scanning and the same LED
layout, so a single `keymap.c` serves both -- but a rev B image flashed at rev
A's address (or vice versa) will not boot.

## Build

From `zsa-config-monnlander/`, the Makefile is the normal entry point. It reads
the revision off the attached board, so neither target has to be told which one
to target, and it skips the compile when the keymap has not changed:

```
make build      # compile, if the keymap changed since last time
make flash      # build if needed, then flash the attached board
make help       # what it would do right now, and for which revision
make clean      # discard this keymap's build tree, both revisions
```

With no board attached it falls back to rev B; `REV=reva` / `REV=revb`
overrides the detection. What it runs underneath is:

```
qmk compile -kb zsa/moonlander/revb -km ZQgpz
```

`-kb zsa/moonlander` alone is rejected — the revision is required.

The keymap lives in this repo and is symlinked into the QMK tree:

```
~/qmk_firmware/keyboards/zsa/moonlander/keymaps/ZQgpz
  -> zsa-config-monnlander/zsa_moonlander_layout_source
```

Do not move or rename `zsa-config-monnlander/` — it breaks that symlink.

## The GCC 16 patch (load-bearing)

`keyboards/zsa/moonlander/moonlander.c` uses the `"g"` constraint for the
bootloader-jump inline asm:

```c
__asm__ volatile("msr msp, %0" ::"g"(*(volatile uint32_t *)APP_ADDRESS));
```

`"g"` permits a memory operand, but `msr msp` requires a register. Older GCC
happened to pick a register; GCC 16 picks `[r3]` and the assembler fails with:

```
Error: Thumb encoding does not support an immediate here -- `msr msp,[r3]'
```

Fix is `"g"` → `"r"`. Applied to the local QMK clone, **not** this repo, so a
`git pull` in `~/qmk_firmware` reverts it and builds break again. Reapply:

```
git -C ~/qmk_firmware apply /path/to/tools/patches/qmk-gcc16-msp-constraint.patch
```

The same bug exists in `keyboards/zsa/ergodox_ez/stm32/stm32.c` — irrelevant
unless that board is ever built here.

## Flashing

`make flash` does this for whichever revision is attached. Underneath, and when
running it by hand: use `qmk flash`, for **both** revisions. It reads the bootloader type and the
DFU arguments from the board definition, so the address cannot be got wrong by
hand:

```sh
qmk flash -kb zsa/moonlander/reva -km ZQgpz    # or revb
```

Press the physical reset button first -- recessed, top-left of the left half,
needs a paperclip. The board then enumerates as its bootloader (`0483:df11` on
rev A, `3297:2003` on rev B) and `qmk flash` proceeds.

If rev A reports `dfuERROR, status(10) = Device's firmware is corrupt` before
writing, that is a stale status left in the bootloader. `qmk flash` clears it
and continues; it is not a failure.

### wally-cli

Works on rev A, **fails on rev B**. The packaged v2.0.0 only knows the older
STM32 DFU id and exits before writing anything:

```
Error while extracting DFU Suffix: Invalid vendor or product id,
expected 0x83:0x11 got 0x97:0x3
```

Nothing is written when this happens, so it is safe -- just use `qmk flash`.

### Flashing a loose binary

When flashing a `.bin` that did not come from `qmk compile`, verify the address
rather than trusting it. The link address is baked into the image:

```sh
arm-none-eabi-objdump -h <firmware>.elf | grep vectors
```

It must match the bootloader's advertised region (`dfu-util -l`). Then:

```sh
# rev A
dfu-util -d 0483:df11 -a 0 -s 0x08000000:leave -D zsa_moonlander_reva_*.bin
# rev B
dfu-util -d 3297:2003 -a 0 -s 0x08002000:leave -D zsa_moonlander_revb_*.bin
```

Neither bootloader is reachable over DFU, and the physical reset button is
hardware, so a bad application image is always recoverable.

## Permissions

`zsa-udev` provides `50-oryx.rules`, `50-oryx-legacy.rules`, `50-wally.rules`
(note: filenames say oryx/wally, not zsa). Vendor `3297` gets `MODE:="0666"`,
so `dfu-util` works without sudo. If it does not, replug the board — udev rules
only apply to device nodes created after they were loaded.

## Toolchain setup

`tools/setup-toolchain.sh`. Idempotent. It preflights by asking the mirror
whether every package is actually fetchable, because on Omarchy the sync
database's *age* is meaningless — the stable mirror is a dated snapshot, so the
db reads as days old even when perfectly current. If packages 404, the fix is
`omarchy update`, never `pacman -Sy` (which would leave a partial upgrade).
