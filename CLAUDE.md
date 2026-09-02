# Keyboards

Two split keyboards kept deliberately in sync so muscle memory transfers
between them. Each board's config is its own repo, tracked here as a submodule
so that a commit in this repo names a *matched pair* of configurations.

| Path | Board | Firmware |
|---|---|---|
| `zmk-config-cornekbh/` | Corne (CorneKBH, wireless) | ZMK |
| `zsa-config-monnlander/` | Moonlander Mark I rev B | QMK (ZSA fork) |

The Corne is the reference implementation. Its layout philosophy is the source
of truth; the Moonlander mirrors it. See `layout/SPEC.md` for the shared
contract and `layout/divergences.md` for differences that are intentional.

## Ground rules

- A layout change to one board is not finished until the other board matches
  or the difference is recorded in `layout/divergences.md`.
- The Moonlander has keys the Corne lacks (number row, inner columns, bottom
  row). These may carry extra functions, but must never *conflict* with a
  Corne binding.
- Timings live in both configs and must agree: 200 / 180 / 120 ms.

## Working here

Board-specific build and flash procedures are in `.claude/skills/`. They are
scoped to this directory and do not load globally.
