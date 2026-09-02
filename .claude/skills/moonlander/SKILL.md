---
name: moonlander
description: Build and flash firmware for the ZSA Moonlander Mark I rev B from source. Use when compiling the QMK keymap, flashing the board, recovering from a bad flash, or setting up the toolchain. Triggers: moonlander, qmk compile, dfu-util, wally, flash keyboard, bootloader.
---

# Moonlander: build and flash

Board is **rev B** (USB `3297:1972`). Confirmed against `revb/keyboard.json` —
rev A is `3297:1969`. Always build the `revb` target.

## Build

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

**`wally-cli` does not work on this board.** The Arch package is v2.0.0 and only
knows the older STM32 DFU id `0483:df11`. This Moonlander has ZSA's newer
"ignition" bootloader, `3297:2003`, and wally exits before writing anything:

```
Error while extracting DFU Suffix: Invalid vendor or product id,
expected 0x83:0x11 got 0x97:0x3
```

Use `dfu-util`. Press the physical reset button (recessed, top-left of the left
half — needs a paperclip), then:

```
dfu-util -d 3297:2003 -a 0 -s 0x08002000:leave -D zsa_moonlander_revb_ZQgpz.bin
```

`0x08002000` is not a guess: the bootloader advertises
`@Internal Flash /0x08002000/124*0002Kg`, and the built ELF's `.vectors`
section loads at exactly that address. Verify before flashing an unfamiliar
binary:

```
arm-none-eabi-objdump -h <firmware>.elf | grep vectors
```

The bootloader lives below `0x08002000` and is not exposed over DFU, so it
cannot be overwritten. The physical reset button is hardware and works
regardless of firmware state — recovery is always possible.

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
