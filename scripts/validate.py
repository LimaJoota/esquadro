#!/usr/bin/env python3
"""Check any SVG for the mistakes that make drawings wrong or unreadable. Standard library only.

    python scripts/validate.py drawing.svg [--static] [--strict] [--json] [--margin 5] [--annotate out.svg]

Errors (exit code 1):
  TEXT_OVERLAP      two pieces of text overlap
  TEXT_CROSSED      a stroke or filled edge runs through text
  OUT_OF_BOUNDS     an element leaves the canvas, the --margin, or the sheet frame
  EXTERNAL_REF      scripts or external files, so the SVG is not self-contained
  DIM_MISMATCH      an Esquadro dimension's printed value disagrees with its geometry and scale
  DIM_NTS_MARK      a not-to-scale dimension has no underline
  NO_SCALE          no declared scale and no "not to scale" notice

Warnings (exit code 0, or 1 with --strict):
  SMALL_TEXT, THIN_STROKE, LOW_CONTRAST, COLOR_ONLY, FONT_NOT_EMBEDDED, TEXT_ESTIMATED, NONSTANDARD_SCALE,
  LEADER_CROSS

Text is measured in a local browser when one is found, and otherwise with bundled font metrics.
"""

from __future__ import annotations

import argparse
import base64
import itertools
import json
import math
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from render import find_browser, run_browser

SVG_NS = "http://www.w3.org/2000/svg"
XLINK = "{http://www.w3.org/1999/xlink}href"
METRICS = json.loads(
    (Path(__file__).resolve().parents[1] / "assets" / "fonts" / "metrics.json").read_text(encoding="utf-8")
)
EMBEDDED_FAMILIES = {"esquadro tech": "overpass", "esquadro sketch": "patrick-hand"}
GENERIC_WIDTH = {"mono": 0.62, "serif": 0.5, "sans": 0.56, "hand": 0.48}
SKIP_TAGS = {
    "defs",
    "symbol",
    "clipPath",
    "mask",
    "marker",
    "pattern",
    "linearGradient",
    "radialGradient",
    "filter",
    "metadata",
    "title",
    "desc",
    "style",
    "script",
}
INHERITED = {
    "fill",
    "stroke",
    "stroke-width",
    "stroke-opacity",
    "fill-opacity",
    "font-size",
    "font-family",
    "text-anchor",
    "dominant-baseline",
    "visibility",
    "paint-order",
    "font-weight",
}
STANDARD_RATIOS = {1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000}
NO_SCALE_RE = re.compile(r"sem\s+escala|not\s+to\s+scale|\bnts\b|fora\s+de\s+escala|esquem[aá]tico", re.IGNORECASE)
SCALE_RE = re.compile(r"(?:escala|scale)\s*:?\s*\d+\s*:\s*\d+|\b1\s*:\s*\d{1,5}\b", re.IGNORECASE)

Matrix = tuple[float, float, float, float, float, float]
Point = tuple[float, float]
IDENTITY: Matrix = (1, 0, 0, 1, 0, 0)


@dataclass
class Shape:
    order: int
    tag: str
    label: str
    segments: list[tuple[Point, Point]]
    stroke: str | None
    stroke_width: float
    fill: str | None
    closed: bool
    role: str | None = None
    clipped: bool = False


@dataclass
class TextItem:
    order: int
    content: str
    corners: list[Point]  # ink box: top-left, top-right, bottom-right, bottom-left
    size: float
    fill: str | None
    halo: bool
    family: str
    attrs: dict = field(default_factory=dict)
    measured: str = "static"


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    where: list[Point] = field(default_factory=list)


# ---- geometry -------------------------------------------------------------------------------------


def mul(a: Matrix, b: Matrix) -> Matrix:
    return (
        a[0] * b[0] + a[2] * b[1],
        a[1] * b[0] + a[3] * b[1],
        a[0] * b[2] + a[2] * b[3],
        a[1] * b[2] + a[3] * b[3],
        a[0] * b[4] + a[2] * b[5] + a[4],
        a[1] * b[4] + a[3] * b[5] + a[5],
    )


def apply(m: Matrix, p: Point) -> Point:
    return (m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5])


def scale_of(m: Matrix) -> float:
    return math.sqrt(abs(m[0] * m[3] - m[1] * m[2])) or 1.0


def parse_transform(value: str | None) -> Matrix:
    out = IDENTITY
    for name, raw in re.findall(r"(\w+)\s*\(([^)]*)\)", value or ""):
        n = [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", raw)]
        if name == "translate":
            step = (1, 0, 0, 1, n[0], n[1] if len(n) > 1 else 0)
        elif name == "scale":
            step = (n[0], 0, 0, n[1] if len(n) > 1 else n[0], 0, 0)
        elif name == "rotate":
            c, s = math.cos(math.radians(n[0])), math.sin(math.radians(n[0]))
            step = (c, s, -s, c, 0, 0)
            if len(n) == 3:
                step = mul(mul((1, 0, 0, 1, n[1], n[2]), step), (1, 0, 0, 1, -n[1], -n[2]))
        elif name == "matrix" and len(n) == 6:
            step = tuple(n)
        elif name == "skewX":
            step = (1, 0, math.tan(math.radians(n[0])), 1, 0, 0)
        elif name == "skewY":
            step = (1, math.tan(math.radians(n[0])), 0, 1, 0, 0)
        else:
            continue
        out = mul(out, step)
    return out


def number(value: object, default: float = 0.0) -> float:
    """SVG length to user units; mm, cm, in, pt and pc are converted at CSS ratios, % falls back."""
    if value is None:
        return default
    match = re.match(r"\s*([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)\s*([a-zA-Z%]*)", str(value))
    if not match:
        return default
    factor = {"": 1, "px": 1, "pt": 96 / 72, "pc": 16, "mm": 96 / 25.4, "cm": 96 / 2.54, "in": 96}.get(match.group(2))
    return default if factor is None else float(match.group(1)) * factor


def flatten_cubic(p0: Point, p1: Point, p2: Point, p3: Point, n: int = 12) -> list[Point]:
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        out.append(
            (
                u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
            )
        )
    return out


def flatten_arc(
    p0: Point, rx: float, ry: float, phi: float, large: bool, sweep: bool, p1: Point, n: int = 16
) -> list[Point]:
    """SVG endpoint arc to polyline, per the implementation notes of the SVG specification."""
    if rx == 0 or ry == 0 or p0 == p1:
        return [p1]
    rx, ry = abs(rx), abs(ry)
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1, y1 = c * dx + s * dy, -s * dx + c * dy
    grow = x1**2 / rx**2 + y1**2 / ry**2
    if grow > 1:
        rx, ry = rx * math.sqrt(grow), ry * math.sqrt(grow)
    num = max(0.0, rx**2 * ry**2 - rx**2 * y1**2 - ry**2 * x1**2)
    den = rx**2 * y1**2 + ry**2 * x1**2
    co = math.sqrt(num / den) * (-1 if large == sweep else 1) if den else 0.0
    cxp, cyp = co * rx * y1 / ry, -co * ry * x1 / rx
    cx = c * cxp - s * cyp + (p0[0] + p1[0]) / 2
    cy = s * cxp + c * cyp + (p0[1] + p1[1]) / 2
    a0 = math.atan2((y1 - cyp) / ry, (x1 - cxp) / rx)
    a1 = math.atan2((-y1 - cyp) / ry, (-x1 - cxp) / rx)
    delta = a1 - a0
    if sweep and delta < 0:
        delta += 2 * math.pi
    elif not sweep and delta > 0:
        delta -= 2 * math.pi
    out = []
    for i in range(1, n + 1):
        a = a0 + delta * i / n
        xr, yr = rx * math.cos(a), ry * math.sin(a)
        out.append((c * xr - s * yr + cx, s * xr + c * yr + cy))
    return out


def path_points(d: str) -> list[list[Point]]:
    """Flatten a path's `d` into one polyline per subpath."""
    tokens = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", d)
    out: list[list[Point]] = []
    cur: list[Point] = []
    i, cmd = 0, ""
    pos = start = (0.0, 0.0)
    prev_ctrl: Point | None = None

    def take(n: int) -> list[float]:
        nonlocal i
        values = [float(t) for t in tokens[i : i + n]]
        i += n
        return values

    while i < len(tokens):
        if re.match(r"[A-Za-z]", tokens[i]):
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    cur.append(start)
                    out.append(cur)
                cur = [start]
                pos = start
                continue
        rel = cmd.islower()
        kind = cmd.upper()
        base = pos if rel else (0.0, 0.0)
        ctrl: Point | None = None
        try:
            if kind == "M":
                x, y = take(2)
                if len(cur) > 1:
                    out.append(cur)
                pos = (base[0] + x, base[1] + y)
                start = pos
                cur = [pos]
                cmd = "l" if rel else "L"
            elif kind == "L":
                x, y = take(2)
                pos = (base[0] + x, base[1] + y)
                cur.append(pos)
            elif kind == "H":
                pos = (base[0] + take(1)[0], pos[1])
                cur.append(pos)
            elif kind == "V":
                pos = (pos[0], base[1] + take(1)[0])
                cur.append(pos)
            elif kind == "C":
                a = take(6)
                c1, c2 = (base[0] + a[0], base[1] + a[1]), (base[0] + a[2], base[1] + a[3])
                end = (base[0] + a[4], base[1] + a[5])
                cur.extend(flatten_cubic(pos, c1, c2, end))
                pos, ctrl = end, c2
            elif kind == "S":
                a = take(4)
                c1 = (2 * pos[0] - prev_ctrl[0], 2 * pos[1] - prev_ctrl[1]) if prev_ctrl else pos
                c2 = (base[0] + a[0], base[1] + a[1])
                end = (base[0] + a[2], base[1] + a[3])
                cur.extend(flatten_cubic(pos, c1, c2, end))
                pos, ctrl = end, c2
            elif kind in "QT":
                if kind == "Q":
                    a = take(4)
                    q = (base[0] + a[0], base[1] + a[1])
                    end = (base[0] + a[2], base[1] + a[3])
                else:
                    a = take(2)
                    q = (2 * pos[0] - prev_ctrl[0], 2 * pos[1] - prev_ctrl[1]) if prev_ctrl else pos
                    end = (base[0] + a[0], base[1] + a[1])
                c1 = (pos[0] + 2 / 3 * (q[0] - pos[0]), pos[1] + 2 / 3 * (q[1] - pos[1]))
                c2 = (end[0] + 2 / 3 * (q[0] - end[0]), end[1] + 2 / 3 * (q[1] - end[1]))
                cur.extend(flatten_cubic(pos, c1, c2, end, 8))
                pos, ctrl = end, q
            elif kind == "A":
                a = take(7)
                end = (base[0] + a[5], base[1] + a[6])
                cur.extend(flatten_arc(pos, a[0], a[1], a[2], bool(a[3]), bool(a[4]), end))
                pos = end
        except (ValueError, IndexError):
            break
        prev_ctrl = ctrl
    if len(cur) > 1:
        out.append(cur)
    return out


def polygon_of_circle(cx: float, cy: float, rx: float, ry: float, n: int = 40) -> list[Point]:
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


def segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    def orient(p: Point, q: Point, r: Point) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def point_in_poly(p: Point, poly: list[Point]) -> bool:
    inside = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1] - a[1]) / (b[1] - a[1]) * (b[0] - a[0]):
            inside = not inside
    return inside


def segment_hits_poly(a: Point, b: Point, poly: list[Point]) -> bool:
    if point_in_poly(a, poly) or point_in_poly(b, poly):
        return True
    return any(segments_intersect(a, b, c, d) for c, d in zip(poly, poly[1:] + poly[:1]))


def polys_overlap(p: list[Point], q: list[Point]) -> bool:
    """Separating axis test for convex polygons."""
    for poly in (p, q):
        for a, b in zip(poly, poly[1:] + poly[:1]):
            nx, ny = b[1] - a[1], a[0] - b[0]
            pp = [nx * v[0] + ny * v[1] for v in p]
            qq = [nx * v[0] + ny * v[1] for v in q]
            if max(pp) <= min(qq) or max(qq) <= min(pp):
                return False
    return True


def shrink(poly: list[Point], amount: float) -> list[Point]:
    """Inset a box given as four corners, so glancing contact does not count."""
    cx, cy = sum(p[0] for p in poly) / 4, sum(p[1] for p in poly) / 4
    width = math.dist(poly[0], poly[1]) or 1
    height = math.dist(poly[1], poly[2]) or 1
    fx = max(0.05, 1 - 2 * amount / width)
    fy = max(0.05, 1 - 2 * amount / height)
    ux, uy = (poly[1][0] - poly[0][0]) / width, (poly[1][1] - poly[0][1]) / width
    vx, vy = (poly[3][0] - poly[0][0]) / height, (poly[3][1] - poly[0][1]) / height
    out = []
    for p in poly:
        du = (p[0] - cx) * ux + (p[1] - cy) * uy
        dv = (p[0] - cx) * vx + (p[1] - cy) * vy
        out.append((cx + ux * du * fx + vx * dv * fy, cy + uy * du * fx + vy * dv * fy))
    return out


def bbox(points: list[Point]) -> tuple[float, float, float, float]:
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


# ---- CSS and presentation --------------------------------------------------------------------------


def local(tag: object) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def parse_css(root: ET.Element) -> list[tuple[str, dict]]:
    rules: list[tuple[str, dict]] = []
    for node in root.iter():
        if local(node.tag) != "style" or not node.text:
            continue
        css = re.sub(r"/\*.*?\*/", "", node.text, flags=re.DOTALL)
        css = re.sub(r"@font-face\s*\{[^}]*\}", "", css)
        for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            decl = parse_decl(body)
            for selector in selectors.split(","):
                rules.append((selector.strip(), decl))
    return rules


def parse_decl(body: str) -> dict:
    out = {}
    for item in body.split(";"):
        if ":" in item:
            key, value = item.split(":", 1)
            out[key.strip().lower()] = value.strip()
    shorthand = out.pop("font", None)
    if shorthand:
        match = re.search(r"([\d.]+(?:px|pt|mm|em|rem)?)(?:/[\d.a-z%]+)?\s+(.+)$", shorthand)
        if match:
            out.setdefault("font-size", match.group(1))
            out.setdefault("font-family", match.group(2))
    return out


def selector_matches(selector: str, node: ET.Element) -> bool:
    """Simple selectors only: tag, .class, #id and combinations; the last compound of a chain decides."""
    last = selector.split()[-1] if selector else ""
    match = re.fullmatch(r"([a-zA-Z][\w-]*)?((?:[.#][\w-]+)*)", last)
    if not match:
        return False
    tag, rest = match.groups()
    if tag and tag != local(node.tag):
        return False
    classes = set((node.get("class") or "").split())
    for sigil, name in re.findall(r"([.#])([\w-]+)", rest or ""):
        if sigil == "." and name not in classes:
            return False
        if sigil == "#" and node.get("id") != name:
            return False
    return bool(tag or rest)


def presentation(node: ET.Element, inherited: dict, rules: list[tuple[str, dict]]) -> dict:
    out = dict(inherited)
    for key in INHERITED | {"display", "opacity", "filter", "clip-path"}:
        if node.get(key) is not None:
            out[key] = node.get(key)
    for selector, decl in rules:
        if selector_matches(selector, node):
            out.update(decl)
    out.update(parse_decl(node.get("style") or ""))
    return out


def paint(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    return None if text in ("none", "transparent") else text


def luminance(color: str | None) -> float | None:
    """Relative lightness 0..1 for hex, rgb() and a few names; None when unknown."""
    if not color:
        return None
    names = {"black": "#000", "white": "#fff", "gray": "#808080", "grey": "#808080", "red": "#f00", "blue": "#00f"}
    names |= {"green": "#008000", "yellow": "#ff0", "orange": "#ffa500", "silver": "#c0c0c0", "lightgray": "#d3d3d3"}
    color = names.get(color, color)
    match = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", color)
    if match:
        h = match.group(1)
        h = "".join(c * 2 for c in h) if len(h) == 3 else h
        r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    else:
        match = re.fullmatch(r"rgb\(\s*(\d+)[ ,]+(\d+)[ ,]+(\d+)\s*\)", color)
        if not match:
            return None
        r, g, b = (int(v) / 255 for v in match.groups())
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ---- document walk --------------------------------------------------------------------------------


class Document:
    def __init__(self, raw: str) -> None:
        if re.search(r"<!ENTITY", raw, re.IGNORECASE):
            raise ValueError("SVG declares XML entities; refusing to parse")
        self.raw = raw
        self.root = ET.fromstring(raw)
        if local(self.root.tag) != "svg":
            raise ValueError("root element is not <svg>")
        self.rules = parse_css(self.root)
        self.ids = {n.get("id"): n for n in self.root.iter() if n.get("id")}
        self.shapes: list[Shape] = []
        self.texts: list[TextItem] = []
        self.order = 0
        self.width, self.height = self._canvas()
        self.base = self._viewbox_matrix()
        self.frame: tuple[float, float, float, float] | None = None
        self._walk(self.root, IDENTITY, {}, False, 0)

    def _canvas(self) -> tuple[float, float]:
        box = self.root.get("viewBox")
        if box:
            parts = [float(x) for x in re.split(r"[\s,]+", box.strip())]
            self.vb_x, self.vb_y = parts[0], parts[1]
            return parts[2], parts[3]
        self.vb_x, self.vb_y = 0.0, 0.0
        return number(self.root.get("width"), 300.0), number(self.root.get("height"), 150.0)

    def _viewbox_matrix(self) -> Matrix:
        return (1, 0, 0, 1, -self.vb_x, -self.vb_y)

    @property
    def paper_mm_per_unit(self) -> float | None:
        """Physical millimetres per user unit, when the root states a physical width."""
        width = self.root.get("width") or ""
        match = re.match(r"\s*([\d.]+)\s*(mm|cm|in)\s*$", width)
        if not match or not self.width:
            return None
        mm = float(match.group(1)) * {"mm": 1, "cm": 10, "in": 25.4}[match.group(2)]
        return mm / self.width

    def _walk(self, node: ET.Element, ctm: Matrix, inherited: dict, clipped: bool, depth: int) -> None:
        if depth > 64:
            return
        tag = local(node.tag)
        if tag in SKIP_TAGS:
            return
        style = presentation(node, inherited, self.rules)
        if style.get("display") == "none" or style.get("visibility") == "hidden":
            return
        matrix = mul(ctm, parse_transform(node.get("transform")))
        clipped = clipped or bool(style.get("clip-path"))
        style = {k: v for k, v in style.items() if k in INHERITED or k in ("display", "opacity", "filter", "clip-path")}
        if tag in ("line", "rect", "circle", "ellipse", "polyline", "polygon", "path"):
            self._shape(node, tag, matrix, style, clipped)
        elif tag == "text":
            self._text(node, matrix, style)
            return
        elif tag == "use":
            target = self.ids.get((node.get("href") or node.get(XLINK) or "").lstrip("#"))
            if target is not None:
                shifted = mul(matrix, (1, 0, 0, 1, number(node.get("x")), number(node.get("y"))))
                if local(target.tag) == "symbol":
                    for child in target:
                        self._walk(child, shifted, style, clipped, depth + 1)
                else:
                    self._walk(target, shifted, style, clipped, depth + 1)
            return
        for child in node:
            self._walk(child, matrix, style, clipped, depth + 1)

    def _shape(self, node: ET.Element, tag: str, m: Matrix, style: dict, clipped: bool) -> None:
        get = lambda key, default=0.0: number(node.get(key), default)
        subpaths: list[list[Point]] = []
        closed = False
        if tag == "line":
            subpaths = [[(get("x1"), get("y1")), (get("x2"), get("y2"))]]
        elif tag == "rect":
            x, y, w, h = get("x"), get("y"), get("width"), get("height")
            if w <= 0 or h <= 0:
                return
            subpaths, closed = [[(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]], True
        elif tag == "circle":
            subpaths, closed = [polygon_of_circle(get("cx"), get("cy"), get("r"), get("r"))], True
        elif tag == "ellipse":
            subpaths, closed = [polygon_of_circle(get("cx"), get("cy"), get("rx"), get("ry"))], True
        elif tag in ("polyline", "polygon"):
            nums = [float(v) for v in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", node.get("points") or "")]
            pts = list(zip(nums[0::2], nums[1::2]))
            if tag == "polygon" and pts:
                pts.append(pts[0])
                closed = True
            subpaths = [pts]
        elif tag == "path":
            subpaths = path_points(node.get("d") or "")
            closed = "z" in (node.get("d") or "").lower()
        segments = []
        for sub in subpaths:
            world = [apply(m, p) for p in sub]
            segments.extend((a, b) for a, b in itertools.pairwise(world) if a != b)
        if not segments:
            return
        stroke = paint(style.get("stroke"))
        fill = paint(style.get("fill", "#000"))
        if float(style.get("opacity", 1) or 1) == 0:
            return
        self.order += 1
        self.shapes.append(
            Shape(
                self.order,
                tag,
                node.get("id") or tag,
                segments,
                stroke,
                number(style.get("stroke-width"), 1.0) * scale_of(m),
                fill,
                closed,
                node.get("data-esq-role"),
                clipped,
            )
        )
        if node.get("data-esq-role") == "frame":
            self.frame = bbox([p for seg in segments for p in seg])

    def _text(self, node: ET.Element, m: Matrix, style: dict) -> None:
        self.order += 1
        chunks = self._text_chunks(node, style)
        order = self.order
        for content, x, y, chunk_style in chunks:
            size = font_size(chunk_style)
            item = TextItem(
                order,
                content,
                [],
                size * scale_of(m),
                paint(chunk_style.get("fill", "#000")),
                bool(paint(chunk_style.get("stroke"))) and "stroke" in str(chunk_style.get("paint-order", "")),
                str(chunk_style.get("font-family", "")),
                dict(node.attrib),
            )
            item.corners = static_box(content, x, y, size, chunk_style, m)
            self.texts.append(item)

    def _text_chunks(self, node: ET.Element, style: dict) -> list[tuple[str, float, float, dict]]:
        """One record per visual line: <text> with tspans that set x or dy start a new line."""
        chunks: list[tuple[str, float, float, dict]] = []
        cursor = [number(first_of(node.get("x"))), number(first_of(node.get("y")))]

        def walk(el: ET.Element, inherited: dict) -> None:
            current = presentation(el, inherited, self.rules)
            own_x, own_y, own_dy = el.get("x"), el.get("y"), el.get("dy")
            if own_x is not None:
                cursor[0] = number(first_of(own_x))
            if own_y is not None:
                cursor[1] = number(first_of(own_y))
            if own_dy is not None:
                cursor[1] += length_in_em(first_of(own_dy), font_size(current))
            if el.get("dx") is not None:
                cursor[0] += length_in_em(first_of(el.get("dx")), font_size(current))
            text = (el.text or "").strip()
            if text:
                chunks.append((text, cursor[0], cursor[1], current))
                if own_x is None:
                    cursor[0] += estimated_width(text, font_size(current), current)
            for child in el:
                if local(child.tag) == "tspan":
                    walk(child, current)
                tail = (child.tail or "").strip()
                if tail:
                    chunks.append((tail, cursor[0], cursor[1], current))

        walk(node, style)
        return chunks


def first_of(value: str | None) -> str | None:
    return re.split(r"[\s,]+", value.strip())[0] if value else value


def length_in_em(value: str | None, size: float) -> float:
    if value is None:
        return 0.0
    if value.strip().endswith("em"):
        return float(value.strip()[:-2] or 0) * size
    return number(value)


def font_size(style: dict) -> float:
    raw = str(style.get("font-size", "16"))
    if raw.endswith("em") and not raw.endswith("rem"):
        return float(raw[:-2]) * 16
    if raw.endswith("%"):
        return float(raw[:-1]) * 0.16
    return number(raw, 16.0)


def font_key(style: dict) -> tuple[str | None, str]:
    family = str(style.get("font-family", "")).replace('"', "").replace("'", "").lower()
    first = family.split(",")[0].strip()
    if first in EMBEDDED_FAMILIES:
        return EMBEDDED_FAMILIES[first], "embedded"
    if any(w in family for w in ("mono", "courier", "consolas", "menlo")):
        return None, "mono"
    if any(w in family for w in ("cursive", "caveat", "hand", "comic", "patrick", "kalam", "virgil")):
        return None, "hand"
    if any(w in family for w in ("serif", "times", "georgia")) and "sans" not in family:
        return None, "serif"
    return None, "sans"


def estimated_width(text: str, size: float, style: dict) -> float:
    key, generic = font_key(style)
    factor = 1.15 if str(style.get("font-weight", "")).lower() in ("bold", "700", "800", "900") else 1.0
    if key:
        metric = METRICS[key]
        return sum(metric["widths"].get(c, metric["default"]) for c in text) * size * factor
    return len(text) * GENERIC_WIDTH[generic] * size * factor


def static_box(text: str, x: float, y: float, size: float, style: dict, m: Matrix) -> list[Point]:
    width = estimated_width(text, size, style)
    anchor = style.get("text-anchor", "start")
    start = x - {"start": 0.0, "middle": width / 2, "end": width}.get(anchor, 0.0)
    baseline = style.get("dominant-baseline", "")
    if baseline in ("middle", "central"):
        y += 0.35 * size
    elif baseline in ("hanging", "text-before-edge"):
        y += 0.75 * size
    top = y - 0.72 * size
    bottom = y + 0.12 * size
    return [apply(m, p) for p in ((start, top), (start + width, top), (start + width, bottom), (start, bottom))]


# ---- browser measurement ---------------------------------------------------------------------------

MEASURE_JS = r"""
(async () => {
  await document.fonts.ready;
  const svg = document.querySelector('svg');
  const root = svg.getScreenCTM().inverse();
  const out = [];
  for (const el of svg.querySelectorAll('text')) {
    if (el.closest('defs,symbol,clipPath,mask,pattern,marker')) { out.push(null); continue; }
    const m = root.multiply(el.getScreenCTM());
    const n = el.getNumberOfChars();
    const lines = [];
    let cur = null;
    for (let i = 0; i < n; i++) {
      let s, e;
      try { s = el.getStartPositionOfChar(i); e = el.getEndPositionOfChar(i); } catch (x) { continue; }
      if (!cur || Math.abs(s.y - cur.y) > 0.01 || Math.abs(s.x - cur.x2) > Math.max(cur.h, 1) * 0.6) {
        cur = {x1: s.x, x2: e.x, y: s.y, h: 0}; lines.push(cur);
      } else { cur.x2 = e.x; }
      cur.h = parseFloat(getComputedStyle(el).fontSize);
    }
    out.push({matrix: [m.a, m.b, m.c, m.d, m.e, m.f], lines});
  }
  const pre = document.createElement('pre');
  pre.id = 'esq-result';
  pre.textContent = btoa(unescape(encodeURIComponent(JSON.stringify(out))));
  document.documentElement.appendChild(pre);
})();
"""


def browser_measure(doc: Document) -> bool:
    """Replace text boxes with what a real browser lays out. Returns False if unavailable or refused."""
    browser = find_browser()
    if browser is None or external_references(doc):
        return False
    page = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0}</style></head><body>"
        + re.sub(r"^<\?xml[^>]*\?>", "", doc.raw.lstrip())
        + "<script>"
        + MEASURE_JS
        + "</script></body></html>"
    )
    with tempfile.TemporaryDirectory(prefix="esquadro-measure-") as tmp:
        path = Path(tmp) / "measure.html"
        path.write_text(page, encoding="utf-8")
        try:
            result = run_browser(browser, ["--virtual-time-budget=5000", "--dump-dom", path.as_uri()], timeout=60)
        except (OSError, subprocess.SubprocessError):
            return False
    match = re.search(r'<pre id="esq-result">([^<]+)</pre>', result.stdout)
    if not match:
        return False
    data = json.loads(base64.b64decode(match.group(1)).decode("utf-8"))
    groups: dict[int, list[TextItem]] = {}
    for item in doc.texts:
        groups.setdefault(item.order, []).append(item)
    ordered = sorted(groups)
    measured = [entry for entry in data if entry is not None]
    if len(measured) != len(ordered):
        return False
    new_texts: list[TextItem] = []
    for order, entry in zip(ordered, measured):
        items = groups[order]
        lines = entry["lines"]
        matrix = tuple(entry["matrix"])
        if not lines:
            new_texts.extend(items)
            continue
        template = items[0]
        for k, line in enumerate(lines):
            source = items[k] if k < len(items) else template
            size = line["h"] or source.size
            corners = [
                apply(matrix, p)
                for p in (
                    (line["x1"], line["y"] - 0.72 * size),
                    (line["x2"], line["y"] - 0.72 * size),
                    (line["x2"], line["y"] + 0.12 * size),
                    (line["x1"], line["y"] + 0.12 * size),
                )
            ]
            new_texts.append(
                TextItem(
                    source.order,
                    source.content,
                    corners,
                    source.size,
                    source.fill,
                    source.halo,
                    source.family,
                    source.attrs,
                    "browser",
                )
            )
    doc.texts = new_texts
    return True


# ---- checks ---------------------------------------------------------------------------------------


def external_references(doc: Document) -> list[str]:
    found = []
    for node in doc.root.iter():
        tag = local(node.tag)
        if tag in ("script", "foreignObject"):
            found.append(f"<{tag}>")
        for key, value in node.attrib.items():
            name = key.rsplit("}", 1)[-1]
            if name.startswith("on"):
                found.append(f"{tag} {name}=")
            if name in ("href", "src") and not value.startswith(("#", "data:")):
                found.append(f"{tag} {name}={value[:60]}")
    css = re.sub(r"data:[^)\"']+", "data:", "".join(n.text or "" for n in doc.root.iter() if local(n.tag) == "style"))
    for link in re.findall(r"url\(\s*['\"]?([^)'\"]+)", css):
        if not link.startswith(("#", "data:")):
            found.append(f"css url({link[:60]})")
    found.extend(f"css @import {m[:60]}" for m in re.findall(r"@import\s+([^;]+);", css))
    for node in doc.root.iter():
        for key in ("fill", "stroke", "filter", "clip-path", "mask"):
            value = node.get(key) or ""
            link = re.match(r"\s*url\(\s*['\"]?([^)'\"]+)", value)
            if link and not link.group(1).startswith("#"):
                found.append(f"{key} url({link.group(1)[:60]})")
    return found


def covered_by_knockout(text: TextItem, seg_order: int, doc: Document) -> bool:
    """A filled shape painted after the stroke and before the text hides the stroke behind the text."""
    if text.halo and seg_order < text.order:
        return True
    box = bbox(text.corners)
    for shape in doc.shapes:
        if not (seg_order < shape.order < text.order) or not shape.closed or not shape.fill:
            continue
        pts = [p for seg in shape.segments for p in seg]
        b = bbox(pts)
        if b[0] <= box[0] + 0.01 and b[1] <= box[1] + 0.01 and b[2] >= box[2] - 0.01 and b[3] >= box[3] - 0.01:
            return True
    return False


def filtered(shape: Shape) -> bool:
    return shape.role in ("underline", "frame", "centering-mark") or shape.label == "esq-paper"


def check_text_overlap(doc: Document, tol: float, issues: list[Issue]) -> None:
    boxes = [shrink(t.corners, tol) for t in doc.texts]
    for i, a in enumerate(doc.texts):
        for j in range(i + 1, len(doc.texts)):
            if polys_overlap(boxes[i], boxes[j]):
                b = doc.texts[j]
                issues.append(
                    Issue("error", "TEXT_OVERLAP", f'"{a.content}" overlaps "{b.content}"', [center(a), center(b)])
                )


def center(text: TextItem) -> Point:
    return (sum(p[0] for p in text.corners) / 4, sum(p[1] for p in text.corners) / 4)


def check_text_crossed(doc: Document, tol: float, issues: list[Issue]) -> None:
    for text in doc.texts:
        poly = shrink(text.corners, tol)
        box = bbox(poly)
        for shape in doc.shapes:
            if filtered(shape):
                continue
            has_edge = shape.stroke or (shape.fill and shape.fill not in ("#fff", "#ffffff", "white"))
            if not has_edge:
                continue
            if shape.order > text.order and shape.fill and shape.closed and not shape.stroke:
                continue
            hit = None
            for a, b in shape.segments:
                if max(a[0], b[0]) < box[0] or min(a[0], b[0]) > box[2]:
                    continue
                if max(a[1], b[1]) < box[1] or min(a[1], b[1]) > box[3]:
                    continue
                if segment_hits_poly(a, b, poly):
                    hit = (a, b)
                    break
            if hit and not covered_by_knockout(text, shape.order, doc):
                issues.append(
                    Issue(
                        "error",
                        "TEXT_CROSSED",
                        f'{shape.label} crosses "{text.content}" near ({center(text)[0]:.1f}, {center(text)[1]:.1f})',
                        [center(text)],
                    )
                )
                break


def check_bounds(doc: Document, margin: float, tol: float, issues: list[Issue]) -> None:
    x0, y0, x1, y1 = doc.vb_x + margin, doc.vb_y + margin, doc.vb_x + doc.width - margin, doc.vb_y + doc.height - margin

    def outside(b: tuple[float, float, float, float], limit: tuple[float, float, float, float]) -> bool:
        return b[0] < limit[0] - tol or b[1] < limit[1] - tol or b[2] > limit[2] + tol or b[3] > limit[3] + tol

    for shape in doc.shapes:
        if shape.clipped or shape.label == "esq-paper" or shape.role == "centering-mark":
            continue
        has_ink = shape.stroke or shape.fill
        if not has_ink:
            continue
        half = shape.stroke_width / 2 if shape.stroke else 0.0
        pts = [p for seg in shape.segments for p in seg]
        center_line = bbox(pts)
        b = (center_line[0] - half, center_line[1] - half, center_line[2] + half, center_line[3] + half)
        if shape.fill in ("#fff", "#ffffff", "white") and not shape.stroke:
            continue
        if outside(b, (x0, y0, x1, y1)) and not (margin and shape.role == "frame"):
            issues.append(
                Issue(
                    "error",
                    "OUT_OF_BOUNDS",
                    f"{shape.label} extends to ({b[0]:.1f}, {b[1]:.1f})-({b[2]:.1f}, {b[3]:.1f}) on a "
                    f"{doc.width:g}x{doc.height:g} canvas",
                    [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)],
                )
            )
        elif doc.frame and shape.role != "frame" and outside(center_line, doc.frame):
            issues.append(
                Issue(
                    "error",
                    "OUT_OF_BOUNDS",
                    f"{shape.label} leaves the sheet frame",
                    [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)],
                )
            )
    for text in doc.texts:
        b = bbox(text.corners)
        if outside(b, (x0, y0, x1, y1)):
            issues.append(Issue("error", "OUT_OF_BOUNDS", f'text "{text.content}" leaves the canvas', [center(text)]))
        elif doc.frame and outside(b, doc.frame) and text.attrs.get("data-esq-role") != "scale-note":
            issues.append(
                Issue("error", "OUT_OF_BOUNDS", f'text "{text.content}" leaves the sheet frame', [center(text)])
            )


def check_dimensions(doc: Document, issues: list[Issue]) -> None:
    lines = {s.label: s for s in doc.shapes if s.role == "dimline"}
    underlines = [s for s in doc.shapes if s.role == "underline"]
    for text in doc.texts:
        dim = text.attrs.get("data-esq-dim")
        if not dim:
            continue
        line = lines.get(dim)
        factor = float(text.attrs.get("data-esq-factor", 0) or 0)
        if line is None or factor <= 0:
            issues.append(Issue("error", "DIM_MISMATCH", f'"{text.content}" has no dimension line', [center(text)]))
            continue
        pts = [p for seg in line.segments for p in seg]
        measured = math.dist(pts[0], pts[-1]) / factor
        match = re.search(r"\d+(?:[.,]\d+)?", text.content)
        printed = float(match.group(0).replace(",", ".")) if match else float("nan")
        nts = text.attrs.get("data-esq-nts") == "1"
        if nts:
            ok = any(segment_hits_poly(a, b, grow_down(text.corners)) for s in underlines for a, b in s.segments)
            if not ok:
                issues.append(
                    Issue(
                        "error", "DIM_NTS_MARK", f'"{text.content}" is not to scale but not underlined', [center(text)]
                    )
                )
            continue
        tolerance = max(0.6, measured * 0.005)
        if not abs(printed - measured) <= tolerance:
            issues.append(
                Issue(
                    "error",
                    "DIM_MISMATCH",
                    f'"{text.content}" is printed but the geometry at this scale measures {measured:.1f}',
                    [center(text)],
                )
            )


def check_leaders(doc: Document, issues: list[Issue]) -> None:
    """A leader that crosses a dimension line or another leader is hard to follow."""
    leaders = [s for s in doc.shapes if s.role == "leader"]
    lines = [s for s in doc.shapes if s.role == "dimline"]
    for i, leader in enumerate(leaders):
        for other in lines + leaders[i + 1 :]:
            hit = next(
                (a for a, b in leader.segments for c, d in other.segments if segments_intersect(a, b, c, d)), None
            )
            if hit:
                what = "a dimension line" if other.role == "dimline" else "another leader"
                issues.append(
                    Issue("warning", "LEADER_CROSS", f"a leader crosses {what} near ({hit[0]:.1f}, {hit[1]:.1f})")
                )
                break


def grow_down(corners: list[Point]) -> list[Point]:
    """Text box extended a little past its baseline, where an underline lives."""
    cx, cy = sum(p[0] for p in corners) / 4, sum(p[1] for p in corners) / 4
    return [(cx + (p[0] - cx) * 1.3, cy + (p[1] - cy) * 1.3) for p in corners]


def check_scale(doc: Document, issues: list[Issue]) -> None:
    declared = doc.root.get("data-esq-scale")
    text = " ".join(t.content for t in doc.texts)
    if NO_SCALE_RE.search(text):
        return
    if SCALE_RE.search(text):
        for match in re.finditer(r"\b1\s*:\s*(\d{1,5})\b", text):
            if int(match.group(1)) not in STANDARD_RATIOS:
                issues.append(Issue("warning", "NONSTANDARD_SCALE", f"1:{match.group(1)} is not a recommended ratio"))
        return
    if declared and declared != "none":
        issues.append(Issue("error", "NO_SCALE", f"scale {declared} is declared in metadata but not printed"))
        return
    issues.append(
        Issue(
            "error", "NO_SCALE", 'no scale printed and no "sem escala / not to scale" notice; a reader will measure it'
        )
    )


def check_legibility(
    doc: Document, issues: list[Issue], *, min_text_mm: float = 2.0, min_stroke_mm: float = 0.1
) -> None:
    per_unit = doc.paper_mm_per_unit
    if per_unit:
        small = sorted({round(t.size * per_unit, 2) for t in doc.texts if t.size * per_unit < min_text_mm})
        for value in small:
            sample = next(t for t in doc.texts if round(t.size * per_unit, 2) == value)
            issues.append(
                Issue("warning", "SMALL_TEXT", f'"{sample.content}" prints at {value} mm high', [center(sample)])
            )
        thin = [s for s in doc.shapes if s.stroke and s.stroke_width * per_unit < min_stroke_mm]
        if thin:
            issues.append(Issue("warning", "THIN_STROKE", f"{len(thin)} strokes print under {min_stroke_mm} mm"))
    light = sorted({t.fill for t in doc.texts if (luminance(t.fill) or 0) > 0.55 and not t.halo})
    for color in light:
        issues.append(Issue("warning", "LOW_CONTRAST", f"text in {color} prints faint in black and white"))
    colors = {s.stroke for s in doc.shapes if s.stroke} | {t.fill for t in doc.texts if t.fill}
    colored = [c for c in colors if is_chromatic(c)]
    for i, a in enumerate(colored):
        for b in colored[i + 1 :]:
            la, lb = luminance(a), luminance(b)
            if la is not None and lb is not None and abs(la - lb) < 0.1:
                issues.append(Issue("warning", "COLOR_ONLY", f"{a} and {b} look alike on a black-and-white printer"))


def is_chromatic(color: str) -> bool:
    match = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", color)
    if not match:
        return color in ("red", "blue", "green", "yellow", "orange")
    h = match.group(1)
    h = "".join(c * 2 for c in h) if len(h) == 3 else h
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return max(r, g, b) - min(r, g, b) > 24


def check_fonts(doc: Document, issues: list[Issue]) -> None:
    faces = re.findall(r"@font-face\s*\{[^}]*font-family:\s*['\"]?([^;'\"]+)", doc.raw)
    embedded = {f.strip().lower() for f in faces}
    missing = set()
    for text in doc.texts:
        first = text.family.split(",")[0].replace("'", "").replace('"', "").strip().lower()
        if first and first not in embedded:
            missing.add(first)
        if not first:
            missing.add("(default)")
    if missing:
        issues.append(
            Issue(
                "warning",
                "FONT_NOT_EMBEDDED",
                f"font {', '.join(sorted(missing))} is not embedded; text width and layout depend on the reader's machine",
            )
        )


def validate(
    raw: str, *, margin: float = 0.0, tol: float | None = None, browser: bool = True
) -> tuple[list[Issue], dict]:
    doc = Document(raw)
    per_unit = doc.paper_mm_per_unit
    unit_tol = (0.15 / per_unit) if per_unit else 0.6
    tolerance = unit_tol if tol is None else tol
    issues: list[Issue] = []
    refs = external_references(doc)
    for ref in refs:
        issues.append(Issue("error", "EXTERNAL_REF", f"not self-contained: {ref}"))
    measured_by_browser = browser_measure(doc) if browser else False
    if not measured_by_browser:
        issues.append(
            Issue("warning", "TEXT_ESTIMATED", "no browser used: text widths come from font metrics, not real layout")
        )
    check_text_overlap(doc, tolerance, issues)
    check_text_crossed(doc, tolerance, issues)
    check_bounds(doc, margin, tolerance, issues)
    check_dimensions(doc, issues)
    check_leaders(doc, issues)
    check_scale(doc, issues)
    check_legibility(doc, issues)
    check_fonts(doc, issues)
    summary = {
        "texts": len(doc.texts),
        "shapes": len(doc.shapes),
        "measured": "browser" if measured_by_browser else "static",
        "errors": sum(1 for i in issues if i.severity == "error"),
        "warnings": sum(1 for i in issues if i.severity == "warning"),
    }
    return issues, summary


def annotate(raw: str, issues: list[Issue], target: Path) -> None:
    """Copy of the SVG with a red ring on each problem, for looking at the failure."""
    doc = Document(raw)
    r = max(doc.width, doc.height) * 0.012
    marks = []
    for issue in issues:
        if issue.severity != "error":
            continue
        for x, y in issue.where:
            marks.append(
                f'<circle cx="{x + doc.vb_x:.2f}" cy="{y + doc.vb_y:.2f}" r="{r:.2f}" fill="none" stroke="#d00" '
                f'stroke-width="{r / 5:.2f}"/>'
            )
    target.write_text(raw.replace("</svg>", "\n".join(marks) + "\n</svg>"), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("svg", type=Path)
    parser.add_argument("--static", action="store_true", help="skip the browser; use font metrics only")
    parser.add_argument("--strict", action="store_true", help="warnings also fail")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--margin", type=float, default=0.0, help="required clear margin, in SVG user units")
    parser.add_argument("--tol", type=float, default=None, help="contact tolerance, in SVG user units")
    parser.add_argument("--annotate", type=Path, help="write a copy with problems ringed in red")
    args = parser.parse_args(argv)
    try:
        raw = args.svg.read_text(encoding="utf-8")
        issues, summary = validate(raw, margin=args.margin, tol=args.tol, browser=not args.static)
    except (OSError, ValueError, ET.ParseError) as exc:
        sys.stderr.write(f"cannot check {args.svg}: {exc}\n")
        return 2
    if args.annotate:
        annotate(raw, issues, args.annotate)
    failed = summary["errors"] > 0 or (args.strict and summary["warnings"] > 0)
    if args.json:
        payload = {
            "file": str(args.svg),
            "ok": not failed,
            "summary": summary,
            "issues": [{"severity": i.severity, "code": i.code, "message": i.message} for i in issues],
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    else:
        for issue in sorted(issues, key=lambda i: i.severity):
            sys.stdout.write(f"{issue.severity.upper():7} {issue.code:18} {issue.message}\n")
        verdict = "FAIL" if failed else "PASS"
        sys.stdout.write(
            f"{verdict} {args.svg.name}: {summary['errors']} errors, {summary['warnings']} warnings "
            f"({summary['texts']} texts, {summary['shapes']} shapes, text measured by {summary['measured']})\n"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
