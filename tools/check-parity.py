#!/usr/bin/env python3
"""Verify the Corne and Moonlander configs still implement the same layout.

Parses both keymaps directly -- no hand-maintained copy of the layout to drift.
Compares the things that actually break muscle memory when they diverge:
combos, tap-hold timings, and layer count.

    python3 tools/check-parity.py

Exit code 0 if the boards agree, 1 if they do not. Suitable for a pre-commit
hook or CI job.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZMK = ROOT / "zmk-config-cornekbh" / "config" / "corne.keymap"
QMK_KEYMAP = ROOT / "zsa-config-monnlander" / "zsa_moonlander_layout_source" / "keymap.c"
QMK_CONFIG = ROOT / "zsa-config-monnlander" / "zsa_moonlander_layout_source" / "config.h"

# Both dialects spell the same character differently. Normalise to the symbol
# itself so the two sides are comparable.
SYMBOL = {
    # ZMK -- note several symbols have two spellings in ZMK itself
    "AT": "@", "HASH": "#", "POUND": "#", "DLLR": "$", "DOLLAR": "$",
    "PRCNT": "%", "PERCENT": "%", "EQUAL": "=", "BSLH": "\\",
    "BACKSLASH": "\\", "ESCAPE": "Esc", "PLUS": "+", "ASTRK": "*",
    "STAR": "*", "UNDER": "_", "KP_MINUS": "-", "MINUS": "-", "SLASH": "/",
    "LEFT_BRACKET": "[", "RIGHT_BRACKET": "]", "DELETE": "Del",
    # QMK
    "KC_AT": "@", "KC_HASH": "#", "KC_DLR": "$", "KC_PERC": "%",
    "KC_EQUAL": "=", "KC_BSLS": "\\", "KC_ESCAPE": "Esc", "KC_PLUS": "+",
    "KC_ASTR": "*", "KC_UNDS": "_", "KC_MINUS": "-", "KC_SLASH": "/",
    "KC_LBRC": "[", "KC_RBRC": "]", "KC_DELETE": "Del",
    # the paren mod-morphs, named differently on each side
    "paraless": "(", "paragreat": ")", "PARA_L": "(", "PARA_R": ")",
}


def norm(tok):
    return SYMBOL.get(tok, tok)


# The two dialects name the same physical key differently.
KEYNAME = {
    "COMMA": ",", "DOT": ".", "FSLH": "/", "SLASH": "/",
    "SEMI": ";", "SQT": "'", "HM_A": "A", "HM_SCLN": ";",
}


def letter(tok):
    """Reduce a binding to the key it sits on: '&hm LSHFT A' -> 'A'."""
    tok = tok.strip()
    if tok in KEYNAME:
        return KEYNAME[tok]
    m = re.match(r"MT\(\s*MOD_\w+\s*,\s*KC_(\w+)\s*\)", tok)
    if m:
        return KEYNAME.get(m.group(1), m.group(1))
    m = re.match(r"KC_(\w+)$", tok)
    if m:
        return KEYNAME.get(m.group(1), m.group(1))
    parts = tok.split()
    if parts and parts[0] == "&kp":
        return KEYNAME.get(parts[1], parts[1])
    if parts and parts[0] == "&hm":          # &hm MOD KEY -> KEY
        return KEYNAME.get(parts[2], parts[2])
    return KEYNAME.get(tok, tok)


# --------------------------------------------------------------------------
# ZMK
# --------------------------------------------------------------------------
def parse_zmk(path):
    src = path.read_text()

    # Base layer bindings, indexed by key position -- combos reference these.
    m = re.search(r"DEF\s*\{.*?bindings\s*=\s*<(.*?)>;", src, re.S)
    body = re.sub(r"//.*", "", m.group(1))
    positions = ["&" + b.strip() for b in body.split("&") if b.strip()]

    # Combos
    combos = {}
    block = re.search(r"combos\s*\{(.*?)\n    \};", src, re.S).group(1)
    for name, inner in re.findall(r"(\w[\w-]*)\s*\{(.*?)\};", block, re.S):
        b = re.search(r"bindings\s*=\s*<&([A-Za-z_][\w-]*)\s*([^>]*)>", inner)
        pos = re.search(r"key-positions\s*=\s*<([^>]*)>", inner)
        if not b or not pos:
            continue
        behaviour, arg = b.group(1), b.group(2).strip()
        out = norm(arg) if behaviour == "kp" else norm(behaviour)
        keys = frozenset(letter(positions[int(p)]) for p in pos.group(1).split())
        combos[keys] = out

    # Timings from the `hm` hold-tap
    hm = re.search(r"hm:\s*homerow_mods\s*\{(.*?)\};", src, re.S).group(1)
    timings = {
        "tapping":   int(re.search(r"tapping-term-ms\s*=\s*<(\d+)>", hm).group(1)),
        "quick_tap": int(re.search(r"quick-tap-ms\s*=\s*<(\d+)>", hm).group(1)),
        "prior_idle": int(re.search(r"require-prior-idle-ms\s*=\s*<(\d+)>", hm).group(1)),
    }

    layers = re.findall(r"\n        (\w+)\s*\{\s*\n\s*display-name", src)
    return combos, timings, layers


# --------------------------------------------------------------------------
# QMK
# --------------------------------------------------------------------------
def parse_qmk(keymap, config):
    src = keymap.read_text()

    arrays = {
        name: [k.strip() for k in body.split(",") if k.strip() != "COMBO_END" and k.strip()]
        for name, body in re.findall(
            r"const uint16_t PROGMEM (\w+)\[\]\s*=\s*\{(.*?)\};", src, re.S)
        if name != "layer_colors"
    }

    combos = {}
    for arr, out in re.findall(r"COMBO\(\s*(\w+)\s*,\s*([^)]+?)\s*\)", src):
        if arr not in arrays:
            continue
        combos[frozenset(letter(k) for k in arrays[arr])] = norm(out.strip())

    cfg = config.read_text()
    def define(name):
        m = re.search(rf"^#define\s+{name}\s+(\d+)", cfg, re.M)
        return int(m.group(1)) if m else None
    timings = {
        "tapping":    define("TAPPING_TERM"),
        "quick_tap":  define("QUICK_TAP_TERM"),
        "prior_idle": define("FLOW_TAP_TERM"),
    }

    # Flavor guard: these must stay undefined to match ZMK tap-preferred.
    bad = [f for f in ("PERMISSIVE_HOLD", "HOLD_ON_OTHER_KEY_PRESS")
           if re.search(rf"^#define\s+{f}\b", cfg, re.M)]

    layers = re.findall(r"\[(\w+)\]\s*=\s*LAYOUT_moonlander", src)
    return combos, timings, layers, bad


def main():
    zc, zt, zl = parse_zmk(ZMK)
    qc, qt, ql, bad = parse_qmk(QMK_KEYMAP, QMK_CONFIG)
    fails = []

    def show(keys):
        return "+".join(sorted(keys))

    # Combos
    missing = {k: v for k, v in zc.items() if k not in qc}
    extra   = {k: v for k, v in qc.items() if k not in zc}
    differ  = {k: (zc[k], qc[k]) for k in zc.keys() & qc.keys() if zc[k] != qc[k]}
    print(f"combos: corne {len(zc)}, moonlander {len(qc)}")
    for k, v in sorted(missing.items(), key=lambda x: show(x[0])):
        fails.append(f"combo {show(k)} -> {v!r} on the Corne, absent on the Moonlander")
    for k, v in sorted(extra.items(), key=lambda x: show(x[0])):
        fails.append(f"combo {show(k)} -> {v!r} on the Moonlander, absent on the Corne")
    for k, (a, b) in sorted(differ.items(), key=lambda x: show(x[0])):
        fails.append(f"combo {show(k)}: Corne gives {a!r}, Moonlander gives {b!r}")
    if not (missing or extra or differ):
        print("  all match")

    # Timings
    print("timings:")
    for key, label in (("tapping", "tapping term"),
                       ("quick_tap", "quick tap"),
                       ("prior_idle", "require prior idle / flow tap")):
        z, q = zt[key], qt[key]
        ok = z == q
        print(f"  {label:30s} corne={z}  moonlander={q}  {'ok' if ok else 'MISMATCH'}")
        if not ok:
            fails.append(f"{label}: Corne {z}, Moonlander {q}")

    for f in bad:
        fails.append(f"{f} is defined; ZMK tap-preferred needs it undefined")

    # Layers
    print(f"layers: corne {len(zl)} {zl}")
    print(f"        moonlander {len(ql)} {ql}")
    if len(zl) != len(ql):
        fails.append(f"layer count: Corne {len(zl)}, Moonlander {len(ql)}")

    print()
    if fails:
        print(f"FAIL ({len(fails)}):")
        for f in fails:
            print(f"  - {f}")
        print("\nIf a difference is deliberate, record it in layout/divergences.md")
        return 1
    print("PASS - the two boards implement the same layout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
