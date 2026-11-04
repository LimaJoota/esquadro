#!/usr/bin/env python3
"""Rebuild the README animation and the social preview. Maintainer tool; needs Pillow and a local browser.

pip install pillow && python tools/build_media.py
"""

from __future__ import annotations

import base64
import re
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from render import find_browser, run_browser

PROMPT = "Sketch why a sink trap keeps the smell out."
VERDICT = "validate.py: PASS, 0 errors, 0 warnings"
WIDTH, HEIGHT = 900, 620


def shot(browser: str, html: str, target: Path, width: int, height: int) -> None:
    page = target.with_suffix(".html")
    page.write_text(html, encoding="utf-8")
    run_browser(
        browser, [f"--window-size={width},{height}", "--hide-scrollbars", f"--screenshot={target}", page.as_uri()]
    )
    page.unlink()


def stage(svg: str, typed: str, status: str = "") -> str:
    data = base64.b64encode(svg.encode("utf-8")).decode() if svg else ""
    picture = f'<img src="data:image/svg+xml;base64,{data}">' if svg else ""
    return (
        "<!doctype html><meta charset=utf-8><style>"
        "html,body{margin:0;background:#fff}"
        ".bar{background:#1e1f24;color:#f2f2f2;font:21px/1.3 Menlo,monospace;padding:16px 22px;height:62px;box-sizing:border-box}"
        ".bar b{color:#8fd18f;font-weight:400}"
        ".pic{height:510px;display:flex;align-items:center;justify-content:center}"
        ".pic img{height:500px}"
        ".foot{font:17px Menlo,monospace;color:#2a7d2a;padding:0 22px;height:48px}"
        f"</style><div class=bar><b>&gt;</b> {typed}</div><div class=pic>{picture}</div><div class=foot>{status}</div>"
    )


def layers(svg: str) -> dict:
    """Split the SVG's drawing lines by what they are, keeping the wrapper, so it can build up in stages."""
    rows = svg.split("\n")
    pens = ("#b3001b", "#2563c9")
    role: dict[int, str] = {}
    group = ""
    for i, row in enumerate(rows):
        if row.startswith('<g id="'):
            group = re.match(r'<g id="([^"]+)"', row).group(1)
            continue
        if row == "</g>":
            group = ""
            continue
        if not group or group == "esq-knockouts":
            continue
        if 'data-esq-role="wash"' in row:
            role[i] = "wash"
        elif any(p in row for p in pens):
            role[i] = "pen"
        elif group == "esq-text":
            role[i] = "text"
        else:
            role[i] = "pencil"
    return {"rows": rows, "role": role}


def compose(parts: dict, keep: dict) -> str:
    """`keep` maps a role to how many of its lines to show."""
    seen: dict[str, int] = {}
    out = []
    for i, row in enumerate(parts["rows"]):
        kind = parts["role"].get(i)
        if kind:
            seen[kind] = seen.get(kind, 0) + 1
            if seen[kind] > keep.get(kind, 0):
                continue
        out.append(row)
    return "\n".join(out)


def animation(browser: str, tmp: Path) -> None:
    parts = layers((ROOT / "examples/explain_cut_en.svg").read_text(encoding="utf-8"))
    counts = {k: sum(1 for v in parts["role"].values() if v == k) for k in ("pencil", "text", "pen", "wash")}
    frames: list[tuple[str, int]] = []
    for n in (8, 18, 30, len(PROMPT)):
        frames.append((stage("", PROMPT[:n] + ("_" if n < len(PROMPT) else "")), 220))
    frames.append((stage("", PROMPT), 500))
    for f in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0):
        frames.append((stage(compose(parts, {"pencil": int(counts["pencil"] * f)}), PROMPT), 200))
    base = {"pencil": counts["pencil"]}
    frames.append((stage(compose(parts, {**base, "text": counts["text"]}), PROMPT), 500))
    frames.append((stage(compose(parts, {**base, "text": counts["text"], "pen": counts["pen"]}), PROMPT), 600))
    full = {**base, "text": counts["text"], "pen": counts["pen"], "wash": counts["wash"]}
    frames.append((stage(compose(parts, full), PROMPT), 700))
    frames.append((stage(compose(parts, full), PROMPT, VERDICT), 3500))

    images, durations = [], []
    for i, (html, ms) in enumerate(frames):
        target = tmp / f"f{i:02d}.png"
        shot(browser, html, target, WIDTH, HEIGHT)
        images.append(Image.open(target).convert("RGB").resize((WIDTH * 3 // 4, HEIGHT * 3 // 4), Image.LANCZOS))
        durations.append(ms)
    palette = images[-1].quantize(colors=96, method=Image.MEDIANCUT, dither=Image.NONE)
    quant = [im.quantize(palette=palette, dither=Image.NONE) for im in images]
    quant[0].save(
        ROOT / "assets/demo.gif", save_all=True, append_images=quant[1:], duration=durations, loop=0, optimize=True
    )


def preview(browser: str, tmp: Path) -> None:
    data = base64.b64encode((ROOT / "examples/explain_system_en.svg").read_bytes()).decode()
    font = base64.b64encode((ROOT / "assets/fonts/patrick-hand.woff2").read_bytes()).decode()
    html = (
        "<!doctype html><meta charset=utf-8><style>"
        f"@font-face{{font-family:H;src:url(data:font/woff2;base64,{font})}}"
        "html,body{margin:0;background:#fff;height:640px;overflow:hidden}"
        ".t{position:absolute;left:56px;top:50px;font:96px/1 H;color:#1a1a1a}"
        ".s{position:absolute;left:60px;top:158px;width:430px;font:39px/1.2 H;color:#1a1a1a}"
        ".s em{font-style:normal;color:#b3001b}"
        "img{position:absolute;right:20px;top:40px;width:760px}"
        f"</style><img src='data:image/svg+xml;base64,{data}'><div class=t>Esquadro</div>"
        "<div class=s>Sketches that <em>explain</em>, drawn by your coding agent, and checked before you see them.</div>"
    )
    target = tmp / "preview.png"
    shot(browser, html, target, 1280, 640)
    Image.open(target).convert("RGB").save(ROOT / "assets/social-preview.png", optimize=True)


def main() -> None:
    browser = find_browser()
    if browser is None:
        raise SystemExit("needs Chrome, Chromium or Edge")
    with tempfile.TemporaryDirectory() as raw:
        animation(browser, Path(raw))
        preview(browser, Path(raw))


if __name__ == "__main__":
    main()
