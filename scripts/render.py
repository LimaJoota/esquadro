#!/usr/bin/env python3
"""Render an SVG to PNG or PDF with a local browser, so filters and embedded fonts are honoured.

    python scripts/render.py drawing.svg drawing.png [--dpi 150] [--gray]
    python scripts/render.py drawing.svg drawing.pdf
    python scripts/render.py drawing.svg close.png --dpi 500 --zoom 20,30,40,25

Looks for Chrome, Chromium, Edge or a Playwright Chromium; set ESQUADRO_CHROME to override, and
ESQUADRO_CHROME_ARGS for extra flags, such as --no-sandbox in a container. The browser
runs with a throwaway profile and DNS disabled. SVGs that contain scripts or external references are refused.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MIN_WINDOW = 600.0  # CSS pixels
NO_NETWORK = "--host-resolver-rules=MAP * ~NOTFOUND"
CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
    "msedge",
    "chrome",
)
PLAYWRIGHT_GLOBS = (
    "~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium",
    "~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome",
)
UNSAFE = re.compile(
    r"<script|<foreignObject|\bon\w+\s*=|(?:href|src)\s*=\s*[\"']\s*(?:https?:|file:|//)|url\(\s*['\"]?\s*(?:https?:|file:|//)",
    re.IGNORECASE,
)


def find_browser() -> str | None:
    override = os.environ.get("ESQUADRO_CHROME")
    if override:
        return override
    for candidate in CANDIDATES:
        path = candidate if os.path.isabs(candidate) and os.path.exists(candidate) else shutil.which(candidate)
        if path:
            return path
    for pattern in PLAYWRIGHT_GLOBS:
        found = sorted(glob.glob(os.path.expanduser(pattern)))
        if found:
            return found[-1]
    return None


def physical_size(svg: str) -> tuple[float, float]:
    """Width and height in millimetres, from the root's mm attributes or else its viewBox at 96 dpi."""
    head = svg[svg.lower().find("<svg") :][:2000]
    width = re.search(r'\bwidth="([\d.]+)mm"', head)
    height = re.search(r'\bheight="([\d.]+)mm"', head)
    if width and height:
        return float(width.group(1)), float(height.group(1))
    box = re.search(r'viewBox="[\d.\s,-]*?([\d.]+)[\s,]+([\d.]+)"', head)
    if box:
        return float(box.group(1)) * 25.4 / 96, float(box.group(2)) * 25.4 / 96
    raise ValueError("SVG root needs width/height in mm or a viewBox")


def run_browser(browser: str, args: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory(prefix="esquadro-") as profile:
        command = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            NO_NETWORK,
            f"--user-data-dir={profile}",
        ]
        command += shlex.split(os.environ.get("ESQUADRO_CHROME_ARGS", ""))
        return subprocess.run([*command, *args], capture_output=True, text=True, timeout=timeout, check=False)


def wrap_page(svg: str, width: str, height: str, *, page: str = "", gray: bool = False) -> str:
    svg = re.sub(r"^<\?xml[^>]*\?>", "", svg.lstrip())
    gray_css = "filter:grayscale(1);" if gray else ""
    return (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        f"{page}"
        f"html,body{{margin:0;padding:0;background:#fff;{gray_css}}}"
        f"svg{{display:block;width:{width};height:{height}}}"
        f"</style></head><body>{svg}</body></html>"
    )


def zoomed(svg: str, box: tuple[float, float, float, float]) -> str:
    """The same SVG cut to a region, in the root's own units, so it can be inspected up close."""
    x, y, w, h = box
    return re.sub(
        r'width="[\d.]+mm" height="[\d.]+mm" viewBox="[^"]+"',
        f'width="{w}mm" height="{h}mm" viewBox="{x} {y} {w} {h}"',
        svg,
        count=1,
    )


def render(
    source: Path,
    target: Path,
    *,
    dpi: int = 150,
    gray: bool = False,
    zoom: tuple[float, float, float, float] | None = None,
) -> Path:
    svg = source.read_text(encoding="utf-8")
    if zoom:
        svg = zoomed(svg, zoom)
    if UNSAFE.search(re.sub(r"data:[^)\"']+", "", svg)):
        raise ValueError("SVG contains scripts or external references; run validate.py and remove them first")
    browser = find_browser()
    if browser is None:
        raise RuntimeError("no Chrome, Chromium or Edge found; install one or set ESQUADRO_CHROME")
    w_mm, h_mm = physical_size(svg)
    with tempfile.TemporaryDirectory(prefix="esquadro-page-") as tmp:
        page = Path(tmp) / "page.html"
        url = page.as_uri()
        target = target.resolve()
        if target.suffix.lower() == ".pdf":
            sheet = f"@page{{size:{w_mm}mm {h_mm}mm;margin:0}}"
            page.write_text(wrap_page(svg, f"{w_mm}mm", f"{h_mm}mm", page=sheet, gray=gray), encoding="utf-8")
            result = run_browser(browser, ["--no-pdf-header-footer", f"--print-to-pdf={target}", url])
        else:
            # Chrome will not paint a window below its minimum size, so small drawings are laid
            # out large and the device scale brought down: the output pixels come out the same.
            css_w, css_h = w_mm * 96 / 25.4, h_mm * 96 / 25.4
            grow = max(1.0, MIN_WINDOW / css_w, MIN_WINDOW / css_h)
            win_w, win_h = round(css_w * grow), round(css_h * grow)
            page.write_text(wrap_page(svg, f"{win_w}px", f"{win_h}px", gray=gray), encoding="utf-8")
            result = run_browser(
                browser,
                [
                    f"--window-size={win_w},{win_h}",
                    f"--force-device-scale-factor={dpi / 96 / grow:.5f}",
                    "--hide-scrollbars",
                    "--run-all-compositor-stages-before-draw",
                    "--virtual-time-budget=3000",
                    f"--screenshot={target}",
                    url,
                ],
            )
    if not target.exists():
        raise RuntimeError(f"browser did not write {target}: {result.stderr[-400:]}")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("svg", type=Path)
    parser.add_argument("output", type=Path, help="target .png or .pdf")
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--gray", action="store_true", help="simulate a black-and-white printer")
    parser.add_argument("--zoom", help="x,y,w,h in mm: render only this region, to inspect the line up close")
    args = parser.parse_args(argv)
    try:
        box = tuple(float(v) for v in args.zoom.split(",")) if args.zoom else None
        written = render(args.svg, args.output, dpi=args.dpi, gray=args.gray, zoom=box)
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        sys.stderr.write(f"render failed: {exc}\n")
        return 2
    sys.stdout.write(f"{written}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
