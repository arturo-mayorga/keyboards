#!/usr/bin/env python3
"""Generate SVG layer diagrams and an HTML cheat sheet from the QMK keymap.

The Moonlander counterpart to the Corne's scripts/keymap_cheatsheet.py. Parses
keymap.c directly, so the output cannot drift from the firmware. Re-run after
any keymap change.

    python3 tools/moonlander-cheatsheet.py

Writes docs/moonlander/layer-N-<name>.svg and docs/moonlander/keymap.html.
"""

import html
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYMAP = ROOT / "zsa-config-monnlander" / "zsa_moonlander_layout_source" / "keymap.c"
OUT = ROOT / "docs" / "moonlander"

# Physical geometry, in key units, in LAYOUT argument order. Lifted from
# zsa/moonlander/revb/keyboard.json so this script needs no QMK checkout.
KEYPOS = [
    (0, 0.375, 1), (1, 0.375, 1), (2, 0.125, 1), (3, 0, 1), (4, 0.125, 1), (5, 0.25, 1),
    (6, 0.25, 1), (10, 0.25, 1), (11, 0.25, 1), (12, 0.125, 1), (13, 0, 1), (14, 0.125, 1),
    (15, 0.375, 1), (16, 0.375, 1), (0, 1.375, 1), (1, 1.375, 1), (2, 1.125, 1), (3, 1, 1),
    (4, 1.125, 1), (5, 1.25, 1), (6, 1.25, 1), (10, 1.25, 1), (11, 1.25, 1), (12, 1.125, 1),
    (13, 1, 1), (14, 1.125, 1), (15, 1.375, 1), (16, 1.375, 1), (0, 2.375, 1), (1, 2.375, 1),
    (2, 2.125, 1), (3, 2, 1), (4, 2.125, 1), (5, 2.25, 1), (6, 2.25, 1), (10, 2.25, 1),
    (11, 2.25, 1), (12, 2.125, 1), (13, 2, 1), (14, 2.125, 1), (15, 2.375, 1), (16, 2.375, 1),
    (0, 3.375, 1), (1, 3.375, 1), (2, 3.125, 1), (3, 3, 1), (4, 3.125, 1), (5, 3.25, 1),
    (11, 3.25, 1), (12, 3.125, 1), (13, 3, 1), (14, 3.125, 1), (15, 3.375, 1), (16, 3.375, 1),
    (0, 4.375, 1), (1, 4.375, 1), (2, 4.125, 1), (3, 4, 1), (4, 4.125, 1), (5, 4.5, 2),
    (10, 4.5, 2), (12, 4.125, 1), (13, 4, 1), (14, 4.125, 1), (15, 4.375, 1), (16, 4.375, 1),
    (5, 5.5, 1), (6, 5.5, 1), (7, 5.5, 1), (9, 5.5, 1), (10, 5.5, 1), (11, 5.5, 1),
]

# Keys the Corne does not have -- drawn dimmed, matching the rainbow on hardware.
REMOVABLE = set(range(0, 14)) | {20, 21, 34, 35, 54, 55, 56, 59, 60, 63, 64, 65,
                                 67, 68, 69, 70}

LABEL = {
    "KC_TRANSPARENT": "", "KC_NO": "",
    "KC_GRAVE": "`", "KC_MINUS": "-", "KC_EQUAL": "=", "KC_BSPC": "Bksp",
    "KC_LBRC": "[", "KC_RBRC": "]", "KC_BSLS": "\\", "KC_QUOTE": "'",
    "KC_COMMA": ",", "KC_DOT": ".", "KC_SLASH": "/", "KC_SCLN": ";",
    "KC_ENTER": "Enter", "KC_ESCAPE": "Esc", "KC_TAB": "Tab", "KC_SPACE": "Space",
    "KC_LEFT_SHIFT": "Shift", "KC_LEFT_CTRL": "Ctrl", "KC_LEFT_GUI": "Super",
    "KC_LEFT_ALT": "Alt", "KC_CAPS": "Caps", "KC_DELETE": "Del",
    "KC_PAGE_UP": "PgUp", "KC_PGDN": "PgDn", "KC_HOME": "Home", "KC_END": "End",
    "KC_LEFT": "←", "KC_RIGHT": "→", "KC_UP": "↑", "KC_DOWN": "↓",
    "KC_APPLICATION": "Menu", "CW_TOGG": "CapsWord", "QK_BOOT": "BOOT",
    "KC_EXLM": "!", "KC_AT": "@", "KC_HASH": "#", "KC_DLR": "$", "KC_PERC": "%",
    "KC_CIRC": "^", "KC_AMPR": "&", "KC_ASTR": "*", "KC_LPRN": "(", "KC_RPRN": ")",
    "KC_UNDS": "_", "KC_PLUS": "+", "KC_LCBR": "{", "KC_RCBR": "}", "KC_PIPE": "|",
    "KC_TILD": "~", "PARA_L": "( / <", "PARA_R": ") / >",
    "KC_MS_UP": "M↑", "KC_MS_DOWN": "M↓", "KC_MS_LEFT": "M←", "KC_MS_RIGHT": "M→",
    "KC_MS_BTN1": "Click", "KC_MS_BTN2": "Right", "KC_MS_WH_UP": "Scr↑",
    "KC_MS_WH_DOWN": "Scr↓",
    "HM_A": "A\nShift", "HM_SCLN": ";\nShift",
    "RGB_TOG": "RGB", "RGB_MOD": "RGB+", "RGB_HUI": "Hue+", "RGB_HUD": "Hue-",
    "RGB_VAI": "Bri+", "RGB_VAD": "Bri-",
}

U, GAP, PAD, SPLIT = 56, 6, 20, 40


def label_for(tok):
    tok = tok.strip()
    if tok in LABEL:
        return LABEL[tok]
    m = re.match(r"KC_(\w+)$", tok)
    if m:
        return m.group(1)
    m = re.match(r"MO\((\w+)\)$", tok)
    if m:
        return f"→{m.group(1)}"
    m = re.match(r"LT\((\w+),\s*KC_(\w+)\)$", tok)
    if m:
        return f"{m.group(2).title()}\n→{m.group(1)}"
    m = re.match(r"LGUI\(KC_(\w+)\)$", tok)
    if m:
        return f"Super+{m.group(1)}"
    m = re.match(r"LCTL\(KC_(\w+)\)$", tok)
    if m:
        return f"Ctrl+{m.group(1)}"
    return tok


def parse_layers(path):
    src = re.sub(r"//.*", "", path.read_text())
    layers = []
    for name, body in re.findall(
            r"\[(\w+)\]\s*=\s*LAYOUT_moonlander\((.*?)\n\s*\),", src, re.S):
        toks, depth, cur = [], 0, ""
        for ch in body:
            if ch == "," and depth == 0:
                toks.append(cur.strip()); cur = ""
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            cur += ch
        if cur.strip():
            toks.append(cur.strip())
        toks = [t for t in toks if t]
        if len(toks) != 72:
            sys.exit(f"layer {name}: parsed {len(toks)} keys, expected 72")
        layers.append((name, toks))
    return layers


def svg(name, toks):
    xs = [x + (w - 1) for x, _, w in KEYPOS]
    width = int((max(xs) + 1) * (U + GAP) + SPLIT + PAD * 2)
    height = int((max(y for _, y, _ in KEYPOS) + 1) * (U + GAP) + PAD * 2 + 30)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" font-family="system-ui,sans-serif">',
           '<style>'
           '.k{fill:#fff;stroke:#c8ccd4;stroke-width:1.5;rx:6}'
           '.r{fill:#fdf3e7;stroke:#e8b880}'
           '.t{font-size:12px;fill:#1c1e21;text-anchor:middle}'
           '.s{font-size:10px;fill:#6b7280;text-anchor:middle}'
           '.h{font-size:16px;fill:#1c1e21;font-weight:600}'
           '</style>',
           f'<text x="{PAD}" y="{PAD+14}" class="h">{html.escape(name)}</text>']
    for i, (x, y, w) in enumerate(KEYPOS):
        px = PAD + x * (U + GAP) + (SPLIT if x >= 9 else 0)
        py = PAD + 30 + y * (U + GAP)
        kw = U * w + GAP * (w - 1)
        cls = "k r" if i in REMOVABLE else "k"
        out.append(f'<rect class="{cls}" x="{px}" y="{py}" width="{kw}" height="{U}" rx="6"/>')
        lines = label_for(toks[i]).split("\n")
        cy = py + U / 2 + 4 - (len(lines) - 1) * 6
        for n, ln in enumerate(lines):
            cls_t = "t" if n == 0 else "s"
            out.append(f'<text class="{cls_t}" x="{px + kw/2}" y="{cy + n*13}">'
                       f'{html.escape(ln)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    layers = parse_layers(KEYMAP)
    files = []
    for i, (name, toks) in enumerate(layers):
        f = OUT / f"layer-{i}-{name.lower()}.svg"
        f.write_text(svg(name, toks))
        files.append((name, f.name))
        print(f"  wrote {f.relative_to(ROOT)}")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = "\n".join(
        f'<h2>{html.escape(n)}</h2>\n<img src="{f}" alt="{html.escape(n)} layer">'
        for n, f in files)
    (OUT / "keymap.html").write_text(f"""<!doctype html>
<meta charset="utf-8"><title>Moonlander keymap</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem;max-width:1200px}}
img{{max-width:100%;display:block;margin:.5rem 0 2rem}}
.note{{color:#6b7280;font-size:.9rem}}</style>
<h1>Moonlander keymap</h1>
<p class="note">Generated from keymap.c on {stamp}. Keys shaded amber are the
ones the Corne does not have &mdash; they glow rainbow on the board and are
slated for removal.</p>
{body}
""")
    print(f"  wrote {(OUT / 'keymap.html').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
