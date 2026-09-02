# Intentional divergences

Differences that are deliberate. Anything not listed here is a bug in one of
the two configs.

## Moonlander keeps its extra keys

The Moonlander has ~30 keys the Corne does not: the number row, the inner index
columns, the bottom row, and a fourth thumb key per side. These keep useful
functions rather than being blanked.

Rationale: they are *additive*. Nothing on the Corne maps to these positions, so
no habit formed on one board is contradicted by the other. The risk accepted is
that the number row is available here and not on the Corne — NavNum is the habit
to build, and it works identically on both.

## `End` on the outer right thumb

The Corne places `End` on the outer right thumb. On the Moonlander that role
went to the key previously carrying the Left arrow, which means the Moonlander
loses a dedicated Left arrow on the base layer.

Left arrow remains available on NavNum (on `X`), matching the Corne.

## Bluetooth vs RGB on the System layer

The Corne's System layer carries `&bt` bindings and `studio_unlock`. Neither has
meaning on a wired board, so those positions carry RGB controls on the
Moonlander instead. Function keys and the bootloader key are in the same places
on both.

## Duplicate GUI / Alt on the Moonlander

The Corne puts GUI and Alt on the left thumb. The Moonlander does too, but also
retains them on its bottom row. Harmless duplication; the thumb positions are
the ones that matter for parity.
