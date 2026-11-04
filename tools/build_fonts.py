#!/usr/bin/env python3
"""Rebuild assets/fonts from upstream OFL fonts. Maintainer tool, not needed at runtime.

Requires: pip install fonttools brotli

    python tools/build_fonts.py /path/to/Overpass[wght].ttf /path/to/PatrickHand-Regular.ttf
"""

import json
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

OUT = Path(__file__).resolve().parent.parent / "assets" / "fonts"
EXTRA = "–—‘’“”•…≈≤≥±×÷°µØøŒœ⌀∅→←↑↓√²³¼½¾"
CODEPOINTS = set(range(0x20, 0x7F)) | set(range(0xA0, 0x100)) | {ord(c) for c in EXTRA}


def build(src: str, name: str) -> dict:
    font = TTFont(src)
    if "fvar" in font:
        font = instancer.instantiateVariableFont(font, {"wght": 400})
    options = subset.Options()
    options.layout_features = ["kern", "liga", "mark", "mkmk", "ccmp", "locl"]
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]
    options.notdef_outline = True
    sub = subset.Subsetter(options)
    sub.populate(unicodes=CODEPOINTS)
    sub.subset(font)

    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    os2 = font["OS/2"]
    widths = {chr(cp): round(hmtx[glyph][0] / upem, 4) for cp, glyph in sorted(cmap.items())}
    meta = {
        "cap": round(getattr(os2, "sCapHeight", 0.7 * upem) / upem, 4),
        "x": round(getattr(os2, "sxHeight", 0.5 * upem) / upem, 4),
        "ascent": round(font["hhea"].ascent / upem, 4),
        "descent": round(-font["hhea"].descent / upem, 4),
        "default": round(sum(widths.values()) / len(widths), 4),
        "widths": widths,
    }
    font.flavor = "woff2"
    font.save(OUT / f"{name}.woff2")
    return meta


def main(overpass: str, patrick: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    metrics = {"overpass": build(overpass, "overpass"), "patrick-hand": build(patrick, "patrick-hand")}
    (OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:3])
