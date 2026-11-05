"""Drawing engine: paper-space primitives, modes, sheets and SVG output.

All coordinates here are paper millimetres with y growing downward (SVG convention).
Real-world geometry goes through `view.View`, which applies the scale. Standard library only.
"""

from __future__ import annotations

import base64
import itertools
import json
import math
import random
import re
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

from .pencil import strokes

if TYPE_CHECKING:
    from .view import View

Point = tuple[float, float]
Rect = tuple[float, float, float, float]  # x, y, width, height

VERSION = "0.4.0"
FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
METRICS: dict = json.loads((FONT_DIR / "metrics.json").read_text(encoding="utf-8"))

PAPER = {"A0": (841, 1189), "A1": (594, 841), "A2": (420, 594), "A3": (297, 420), "A4": (210, 297)}
# Recommended scale series (ISO 5455 family).
REDUCTIONS = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000)
ENLARGEMENTS = (50, 20, 10, 5, 2)

STRINGS = {
    "pt": {
        "no_scale": "SEM ESCALA",
        "scale": "ESCALA",
        "title": "TÍTULO",
        "number": "NÚMERO",
        "drawn": "DESENHO",
        "date": "DATA",
        "size": "FOLHA",
        "rev": "REV.",
        "sheet": "PÁG.",
        "units": "UNID.",
        "first_angle": "1º DIEDRO",
        "third_angle": "3º DIEDRO",
    },
    "en": {
        "no_scale": "NOT TO SCALE",
        "scale": "SCALE",
        "title": "TITLE",
        "number": "NUMBER",
        "drawn": "DRAWN",
        "date": "DATE",
        "size": "SIZE",
        "rev": "REV.",
        "sheet": "SHEET",
        "units": "UNITS",
        "first_angle": "1ST ANGLE",
        "third_angle": "3RD ANGLE",
    },
}


@dataclass(frozen=True)
class Scale:
    """Paper-to-real ratio. `declared=False` marks a drawing that is not to any standard scale."""

    paper: float = 1
    real: float = 1
    declared: bool = True

    @property
    def factor(self) -> float:
        return self.paper / self.real

    @classmethod
    def schematic(cls, factor: float) -> Scale:
        return cls(factor, 1, False)

    @classmethod
    def fit(cls, world_w: float, world_h: float, avail_w: float, avail_h: float) -> Scale:
        """Largest recommended scale that fits the geometry in the available paper."""
        for enlarge in ENLARGEMENTS:
            if world_w * enlarge <= avail_w and world_h * enlarge <= avail_h:
                return cls(enlarge, 1)
        for reduce in REDUCTIONS:
            if world_w / reduce <= avail_w and world_h / reduce <= avail_h:
                return cls(1, reduce)
        raise ValueError(f"geometry {world_w}x{world_h} does not fit in {avail_w}x{avail_h} at 1:{REDUCTIONS[-1]}")

    def label(self, lang: str = "en") -> str:
        if not self.declared:
            return STRINGS[lang]["no_scale"]
        return f"{self.paper:g}:{self.real:g}"


@dataclass(frozen=True)
class LineKind:
    width: float
    dash: tuple[float, ...] = ()
    thin_layer: bool = False  # drawn on the annotation layer


@dataclass(frozen=True)
class Style:
    font: str
    family: str
    fallback: str
    ink: str
    sizes: dict
    lines: dict
    arrow: float
    linecap: str


_TECH_LINES = {
    "visible": LineKind(0.5),
    "thin": LineKind(0.25, (), True),
    "hatch": LineKind(0.18),
    "hidden": LineKind(0.25, (3, 1.5)),
    "center": LineKind(0.25, (10, 1.5, 1.5, 1.5), True),
    "phantom": LineKind(0.25, (10, 1.5, 1.5, 1.5, 1.5, 1.5), True),
    "cutting": LineKind(0.25, (10, 1.5, 1.5, 1.5), True),
    "border": LineKind(0.7),
    "signal": LineKind(0.25, (2.5, 1.5), True),
}
# A pencil is a thin, even line: about 0.3 mm on a figure printed at 170 mm wide.
_SKETCH_LINES = {
    "visible": LineKind(0.42),
    "thin": LineKind(0.28, (), True),
    "hatch": LineKind(0.2),
    "hidden": LineKind(0.28, (3, 1.6)),
    "center": LineKind(0.24, (9, 1.6, 1.6, 1.6), True),
    "phantom": LineKind(0.24, (9, 1.6, 1.6, 1.6, 1.6, 1.6), True),
    "cutting": LineKind(0.24, (9, 1.6, 1.6, 1.6), True),
    "border": LineKind(0.5),
    "signal": LineKind(0.28, (2.6, 1.6), True),
}
STYLES = {
    "technical": Style(
        "overpass",
        "Esquadro Tech",
        "'Liberation Sans',Arial,Helvetica,sans-serif",
        "#000",
        {"dim": 2.5, "label": 3.5, "heading": 5, "title": 7},
        _TECH_LINES,
        3.0,
        "butt",
    ),
    "sketch": Style(
        "caveat",
        "Esquadro Sketch",
        "'Bradley Hand','Segoe Print',cursive",
        "#2e2e2e",
        {"dim": 3.5, "label": 3.9, "heading": 5.4, "title": 7.5},
        _SKETCH_LINES,
        2.4,
        "round",
    ),
}
STYLES["industrial"] = STYLES["technical"]


# Pen inks stay distinct in black and white: red prints darker than blue.
PENS = {"red": "#b3001b", "blue": "#2563c9", "black": "#111111"}
WASHES = {
    "blue": "#7fb0e6",
    "red": "#ea8f7f",
    "yellow": "#f4cf5d",
    "green": "#96c98e",
    "brown": "#c9a27a",
    "gray": "#a8adb3",
}

# Sketch finish: hand unsteadiness in mm, corner overshoot, chance of a second pass on a firm line.
FINISHES = {
    "napkin": (0.2, 1.0, 0.8),
    "study": (0.09, 0.35, 0.55),
    "clean": (0.04, 0.1, 0.2),
}
# Tone of each line kind in pencil: firm lines nearly full, construction lines lighter.
PENCIL_TONE = {"visible": 0.92, "border": 0.95, "thin": 0.86, "hatch": 0.62}


class _Ink(str):
    """A pencil mark: runs of these share one grain filter when the SVG is assembled."""


def text_width(text: str, size: float, font: str = "overpass") -> float:
    metric = METRICS[font]
    widths = metric["widths"]
    return sum(widths.get(ch, metric["default"]) for ch in text) * size


def fmt(value: float) -> str:
    """Compact number for SVG attributes."""
    out = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if out in ("-0", "") else out


def format_value(value: float, lang: str = "en", decimals: int | None = None) -> str:
    """Dimension text: whole numbers plain, otherwise rounded, comma decimal in Portuguese."""
    if decimals is None:
        decimals = 0 if abs(value - round(value)) < 0.05 else 1
    out = f"{value:.{decimals}f}"
    return out.replace(".", ",") if lang == "pt" else out


def hatch_segments(rings: Sequence[Sequence[Point]], angle: float, spacing: float) -> list[tuple[Point, Point]]:
    """Clip parallel lines against polygon rings (even-odd), so hatching is real geometry, not a pattern."""
    theta = math.radians(angle)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    def to_local(p: Point) -> Point:
        return (p[0] * cos_t + p[1] * sin_t, -p[0] * sin_t + p[1] * cos_t)

    def to_paper(p: Point) -> Point:
        return (p[0] * cos_t - p[1] * sin_t, p[0] * sin_t + p[1] * cos_t)

    local = [[to_local(p) for p in ring] for ring in rings]
    ys = [p[1] for ring in local for p in ring]
    if not ys:
        return []
    out = []
    y = math.floor(min(ys) / spacing) * spacing + spacing / 2
    while y < max(ys):
        xs = []
        for ring in local:
            for a, b in zip(ring, ring[1:] + ring[:1]):
                if (a[1] <= y) != (b[1] <= y):
                    xs.append(a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]))
        xs.sort()
        for x1, x2 in zip(xs[0::2], xs[1::2]):
            if x2 - x1 > 0.05:
                out.append((to_paper((x1, y)), to_paper((x2, y))))
        y += spacing
    return out


def _rects_overlap(a: Rect, b: Rect, tol: float = 0.0) -> bool:
    return (
        a[0] + tol < b[0] + b[2] and b[0] + tol < a[0] + a[2] and a[1] + tol < b[1] + b[3] and b[1] + tol < a[1] + a[3]
    )


class Drawing:
    """A single SVG figure or sheet. Use `Drawing.sheet()` for framed sheets with a title block."""

    def __init__(
        self,
        width: float,
        height: float,
        mode: str = "technical",
        *,
        lang: str = "en",
        title: str = "",
        description: str = "",
        seed: int = 7,
        wobble: str = "pencil",
        finish: str = "study",
        wash: str | None = None,
        scale_note: bool = True,
    ) -> None:
        if mode not in STYLES:
            raise ValueError(f"unknown mode {mode!r}; use one of {sorted(STYLES)}")
        if wobble not in ("pencil", "geometry", "none"):
            raise ValueError("wobble must be 'pencil', 'geometry' or 'none'")
        if finish not in FINISHES:
            raise ValueError(f"unknown finish {finish!r}; use one of {sorted(FINISHES)}")
        self.finish = finish
        if wash not in (None, "filter", "flat"):
            raise ValueError("wash must be 'filter' or 'flat'")
        self._wash_mode = wash or ("flat" if wobble == "geometry" else "filter")
        self._uses_wash_filter = False
        self._pen: str | None = None
        self.width, self.height = width, height
        self.mode, self.lang = mode, lang
        self.title_text, self.description = title, description
        self.seed = seed
        self.style = STYLES[mode]
        self.sketch = mode == "sketch"
        self.wobble = wobble if self.sketch else "none"
        self.rng = random.Random(seed)
        self.scale_note = scale_note
        self.main_scale: Scale | None = None
        self.area: Rect = (5.0, 5.0, width - 10.0, height - 10.0)
        self._geometry: list[str] = []
        self._annotations: list[str] = []
        self._knockouts: list[str] = []
        self._text: list[str] = []
        self._boxes: list[Rect] = []
        self._dim_count = 0
        self._title_block: dict | None = None
        self._frame: Rect | None = None
        self._finished = False

    @classmethod
    def figure(
        cls, width: str | float = "page", height: float = 95.0, mode: str = "sketch", **kwargs: object
    ) -> Drawing:
        """Figure sized for a document: 'page' is 170 mm, the A4 text width; 'half' is 80 mm; or a width in mm."""
        widths = {"page": 170.0, "half": 80.0}
        return cls(widths.get(width, width) if isinstance(width, str) else float(width), height, mode, **kwargs)

    @classmethod
    def sheet(
        cls,
        size: str = "A3",
        orientation: str = "landscape",
        mode: str = "technical",
        *,
        title_block: dict | None = None,
        frame: str = "iso",
        **kwargs: object,
    ) -> Drawing:
        """Framed sheet. `frame='iso'` is 20 mm left, 10 mm elsewhere; 'nbr-1987' is the older Brazilian layout."""
        short, long_ = PAPER[size]
        width, height = (long_, short) if orientation == "landscape" else (short, long_)
        drawing = cls(width, height, mode, **kwargs)
        if frame == "iso":
            left, right, top, bottom = 20.0, 10.0, 10.0, 10.0
        elif frame == "nbr-1987":
            right = 10.0 if size in ("A0", "A1") else 7.0
            left, top, bottom = 25.0, right, right
        else:
            raise ValueError("frame must be 'iso' or 'nbr-1987'")
        drawing._frame = (left, top, width - left - right, height - top - bottom)
        block = dict(title_block or {})
        block.setdefault("title", drawing.title_text)
        block["_size"] = size
        drawing._title_block = block
        block_h = 26.0
        drawing.area = (left + 4, top + 4, width - left - right - 8, height - top - bottom - block_h - 8)
        return drawing

    # ---- colour ---------------------------------------------------------------------------------

    @property
    def ink(self) -> str:
        return self._pen or self.style.ink

    @contextmanager
    def pen(self, color: str | None) -> Iterator[None]:
        """Draw with a coloured pen inside the block: 'red', 'blue', or any hex. `None` changes nothing."""
        keep = self._pen
        if color is not None:
            self._pen = PENS.get(color, color)
        try:
            yield
        finally:
            self._pen = keep

    def wash(self, pts: Sequence[Point], color: str = "blue", *, strength: float = 1.0) -> None:
        """Watercolour over what is already drawn: pencil shows through. Add it after an outline, before its hatching."""
        fill = WASHES.get(color, color)
        opacity = min(1.0, 0.42 * strength)
        if self._wash_mode == "filter":
            self._uses_wash_filter = True
            coords = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in pts)
            self._geometry.append(
                f'<polygon points="{coords}" fill="{fill}" fill-opacity="{fmt(opacity)}" stroke="{fill}" '
                f'stroke-opacity="{fmt(opacity * 0.6)}" stroke-width="0.5" stroke-linejoin="round" '
                f'filter="url(#{self._wash_filter_id()})" data-esq-role="wash"/>'
            )
            return
        self._geometry.append(
            f'<path d="{self._hand_path(pts, True)}" fill="{fill}" fill-opacity="{fmt(opacity * 0.8)}" '
            'stroke="none" data-esq-role="wash"/>'
        )

    def _wash_filter_id(self) -> str:
        return f"esq-wash-{self.seed}-{self.width:g}x{self.height:g}"

    def _wash_filter(self) -> str:
        """Edges bleed through a slow noise and the pigment pools through another, in the alpha channel only."""
        return (
            f'<filter id="{self._wash_filter_id()}" filterUnits="userSpaceOnUse" x="0" y="0" '
            f'width="{fmt(self.width)}" height="{fmt(self.height)}" color-interpolation-filters="sRGB">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.07" numOctaves="3" seed="{self.seed + 1}" result="edge"/>'
            '<feDisplacementMap in="SourceGraphic" in2="edge" scale="2.2" xChannelSelector="R" '
            'yChannelSelector="G" result="bled"/>'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="4" seed="{self.seed + 2}" result="tone"/>'
            '<feColorMatrix in="tone" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2.1 0 0 0 -0.2" result="pool"/>'
            '<feComposite in="bled" in2="pool" operator="in"/>'
            "</filter>"
        )

    # ---- text -----------------------------------------------------------------------------------

    def size(self, size: float | str) -> float:
        return self.style.sizes[size] if isinstance(size, str) else float(size)

    def measure(self, text: str, size: float | str = "label") -> float:
        return text_width(text, self.size(size), self.style.font)

    def text(
        self,
        pos: Point,
        text: str,
        size: float | str = "label",
        *,
        anchor: str = "start",
        valign: str = "baseline",
        rotate: float = 0,
        knockout: bool = False,
        attrs: str = "",
    ) -> Rect:
        """Place one line of text and return its axis-aligned box. Baselines are computed, never `dominant-baseline`."""
        if not text.strip():
            return (pos[0], pos[1], 0.0, 0.0)
        size_mm = self.size(size)
        metric = METRICS[self.style.font]
        cap = metric["cap"] * size_mm
        x, y = pos
        theta = math.radians(rotate)
        if valign == "middle":
            x += -math.sin(theta) * cap / 2
            y += math.cos(theta) * cap / 2
        elif valign == "top":
            x += -math.sin(theta) * cap
            y += math.cos(theta) * cap
        box = self._text_box((x, y), text, size_mm, anchor, rotate)
        if knockout:
            pad = 0.5
            self._knockouts.append(
                f'<rect x="{fmt(box[0] - pad)}" y="{fmt(box[1] - pad)}" '
                f'width="{fmt(box[2] + 2 * pad)}" height="{fmt(box[3] + 2 * pad)}"/>'
            )
        parts = [f'<text x="{fmt(x)}" y="{fmt(y)}" font-size="{fmt(size_mm)}"']
        if self._pen:
            parts.append(f' fill="{self._pen}"')
        if anchor != "start":
            parts.append(f' text-anchor="{anchor}"')
        if rotate:
            parts.append(f' transform="rotate({fmt(rotate)} {fmt(x)} {fmt(y)})"')
        if attrs:
            parts.append(" " + attrs)
        parts.append(f">{escape(text)}</text>")
        self._text.append("".join(parts))
        self._boxes.append(box)
        return box

    def _text_box(self, pos: Point, text: str, size: float, anchor: str, rotate: float) -> Rect:
        metric = METRICS[self.style.font]
        width = text_width(text, size, self.style.font)
        start = {"start": 0.0, "middle": -width / 2, "end": -width}[anchor]
        corners = [
            (start, -metric["cap"] * size),
            (start + width, -metric["cap"] * size),
            (start + width, 0.2 * size),
            (start, 0.2 * size),
        ]
        theta = math.radians(rotate)
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        pts = [(pos[0] + cx * cos_t - cy * sin_t, pos[1] + cx * sin_t + cy * cos_t) for cx, cy in corners]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def is_free(self, box: Rect) -> bool:
        return not any(_rects_overlap(box, other, 0.05) for other in self._boxes)

    def fit_text(
        self,
        pos: Point,
        text: str,
        max_width: float,
        size: float | str = "label",
        *,
        min_size: float = 2.5,
        **kw: object,
    ) -> Rect:
        """Place text shrunk to fit `max_width`; refuses to go below `min_size` rather than overflow."""
        size_mm = self.size(size)
        width = text_width(text, size_mm, self.style.font)
        if width > max_width:
            size_mm = size_mm * max_width / width
            if size_mm < min_size:
                raise ValueError(f"text {text!r} does not fit {max_width:.1f} mm at {min_size} mm height")
        return self.text(pos, text, size_mm, **kw)

    # ---- strokes --------------------------------------------------------------------------------

    def _kind(self, kind: str) -> LineKind:
        return self.style.lines[kind]

    def _layer(self, kind: str) -> list[str]:
        return self._annotations if self._kind(kind).thin_layer else self._geometry

    def _stroke_attrs(self, kind: str) -> str:
        line = self._kind(kind)
        out = f'stroke-width="{fmt(line.width)}"'
        if self._pen:
            out += f' stroke="{self._pen}"'
        if line.dash:
            out += ' stroke-dasharray="' + " ".join(fmt(d) for d in line.dash) + '"'
        return out

    @property
    def _draws_pencil(self) -> bool:
        return self.wobble in ("pencil", "geometry")

    def _fill_only(self, pts: Sequence[Point], fill: str, kind: str) -> None:
        """The fill of a shape, painted before its pencil outline and free of grain."""
        coords = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in pts)
        self._layer(kind).append(f'<polygon points="{coords}" fill="{fill}" stroke="none"/>')

    def _pencil(self, pts: Sequence[Point], kind: str, *, attrs: str = "") -> None:
        """Draw a path as graphite. A dimension line's exact ends go in an invisible line, for the validator."""
        line = self._kind(kind)
        layer = self._layer(kind)
        identity = re.search(r'\bid="[^"]+"', attrs)
        if identity:
            layer.append(
                f'<line x1="{fmt(pts[0][0])}" y1="{fmt(pts[0][1])}" x2="{fmt(pts[-1][0])}" y2="{fmt(pts[-1][1])}" '
                f'stroke="none" {attrs}/>'
            )
            attrs = attrs.replace(identity.group(0), "").strip()
        unsteady, _, second = FINISHES[self.finish]
        firm = kind in ("visible", "border")
        marks = strokes(
            self.rng,
            pts,
            line.width,
            self.ink,
            PENCIL_TONE.get(kind, 0.82),
            dash=line.dash,
            jitter=unsteady if firm or kind == "hatch" else unsteady * 0.6,
            bow_limit=0.3 if firm else 0.1,
            second_pass=second if firm else 0.0,
            attrs=attrs,
        )
        layer.extend(_Ink(mark) for mark in marks if mark)

    def _grain_id(self) -> str:
        return f"esq-grain-{self.seed}"

    def _grain_filter(self) -> str:
        """Graphite on paper: the edge frays, fine grain breaks the line, and tone drifts along its length."""
        return (
            f'<filter id="{self._grain_id()}" x="-5%" y="-5%" width="110%" height="110%" '
            'color-interpolation-filters="sRGB">'
            f'<feTurbulence type="fractalNoise" baseFrequency="4.5" numOctaves="2" seed="{self.seed}" result="fray"/>'
            '<feDisplacementMap in="SourceGraphic" in2="fray" scale="0.2" xChannelSelector="R" yChannelSelector="G" '
            'result="rough"/>'
            f'<feTurbulence type="fractalNoise" baseFrequency="6.5" numOctaves="3" seed="{self.seed + 3}" result="tooth"/>'
            '<feColorMatrix in="tooth" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3.4 0 0 0 -0.72" '
            'result="grain"/>'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.22" numOctaves="2" seed="{self.seed + 5}" result="drift"/>'
            '<feColorMatrix in="drift" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.1 0 0 0 0.42" '
            'result="tone"/>'
            '<feComposite in="rough" in2="grain" operator="in" result="grainy"/>'
            '<feComposite in="grainy" in2="tone" operator="in"/>'
            "</filter>"
        )

    def _lettering_filter(self) -> str:
        """Lighter than on the lines: letters are small, and they must stay readable."""
        return (
            f'<filter id="{self._grain_id()}-text" x="-2%" y="-2%" width="104%" height="104%" '
            'color-interpolation-filters="sRGB">'
            f'<feTurbulence type="fractalNoise" baseFrequency="5" numOctaves="2" seed="{self.seed + 7}" result="fray"/>'
            '<feDisplacementMap in="SourceGraphic" in2="fray" scale="0.07" xChannelSelector="R" yChannelSelector="G" '
            'result="rough"/>'
            f'<feTurbulence type="fractalNoise" baseFrequency="7" numOctaves="3" seed="{self.seed + 9}" result="tooth"/>'
            '<feColorMatrix in="tooth" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2.2 0 0 0 0.02" '
            'result="grain"/>'
            '<feComposite in="rough" in2="grain" operator="in"/>'
            "</filter>"
        )

    def _assemble(self, layer: list[str]) -> list[str]:
        """Group runs of pencil marks under the grain filter, leaving fills and washes out of it."""
        if self.wobble != "pencil":
            return list(layer)
        out: list[str] = []
        run: list[str] = []

        def flush() -> None:
            if run:
                out.append(f'<g filter="url(#{self._grain_id()})">' + "".join(run) + "</g>")
                run.clear()

        for item in layer:
            if isinstance(item, _Ink):
                run.append(item)
            else:
                flush()
                out.append(item)
        flush()
        return out

    def _hand_path(self, pts: Sequence[Point], closed: bool = False) -> str:
        """Geometry-based tremor: the stroke itself is jittered, so it stays vector everywhere."""
        seq = list(pts) + ([pts[0]] if closed else [])
        out = [f"M{fmt(seq[0][0])} {fmt(seq[0][1])}"]
        for a, b in itertools.pairwise(seq):
            length = math.dist(a, b)
            steps = max(1, int(length / 7))
            nx, ny = (-(b[1] - a[1]) / (length or 1), (b[0] - a[0]) / (length or 1))
            prev = a
            for i in range(1, steps + 1):
                t = i / steps
                wave = 0.0 if i == steps else self.rng.uniform(-0.3, 0.3)
                cur = (a[0] + (b[0] - a[0]) * t + nx * wave, a[1] + (b[1] - a[1]) * t + ny * wave)
                ctrl = ((prev[0] + cur[0]) / 2 + nx * wave * 0.5, (prev[1] + cur[1]) / 2 + ny * wave * 0.5)
                out.append(f"Q{fmt(ctrl[0])} {fmt(ctrl[1])} {fmt(cur[0])} {fmt(cur[1])}")
                prev = cur
        return "".join(out)

    def line(self, p1: Point, p2: Point, kind: str = "visible", *, attrs: str = "", overshoot: bool = True) -> None:
        if self.sketch and overshoot and kind == "visible" and math.dist(p1, p2) > 6:
            length = math.dist(p1, p2)
            ux, uy = (p2[0] - p1[0]) / length, (p2[1] - p1[1]) / length
            push = FINISHES[self.finish][1]
            a, b = self.rng.uniform(0.3, 1.1) * push, self.rng.uniform(0.3, 1.1) * push
            p1, p2 = (p1[0] - ux * a, p1[1] - uy * a), (p2[0] + ux * b, p2[1] + uy * b)
        layer = self._layer(kind)
        extra = f" {attrs}" if attrs else ""
        if self._draws_pencil:
            self._pencil([p1, p2], kind, attrs=attrs)
            return
        layer.append(
            f'<line x1="{fmt(p1[0])}" y1="{fmt(p1[1])}" x2="{fmt(p2[0])}" y2="{fmt(p2[1])}" '
            f"{self._stroke_attrs(kind)}{extra}/>"
        )

    def polyline(
        self,
        pts: Sequence[Point],
        kind: str = "visible",
        *,
        closed: bool = False,
        fill: str | None = None,
        overshoot: bool = False,
    ) -> None:
        """Connected strokes. In sketch mode `overshoot=True` draws crossed corners, like a hand with a ruler."""
        layer = self._layer(kind)
        if self.sketch and overshoot and kind == "visible":
            if fill:
                self._fill_only(pts, fill, kind)
            seq = list(pts) + ([pts[0]] if closed else [])
            for a, b in itertools.pairwise(seq):
                self.line(a, b, kind)
            return
        fill_attr = f'fill="{fill}"' if fill else 'fill="none"'
        if self._draws_pencil:
            if fill:
                self._fill_only(pts, fill, kind)
            self._pencil(list(pts) + ([pts[0], pts[1]] if closed and len(pts) > 1 else []), kind)
            return
        tag = "polygon" if closed else "polyline"
        coords = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in pts)
        layer.append(f'<{tag} points="{coords}" {fill_attr} {self._stroke_attrs(kind)}/>')

    def polygon(self, pts: Sequence[Point], kind: str = "visible", *, fill: str | None = None) -> None:
        self.polyline(pts, kind, closed=True, fill=fill, overshoot=True)

    def rect(self, x: float, y: float, w: float, h: float, kind: str = "visible", *, fill: str | None = None) -> None:
        self.polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], kind, fill=fill)

    def circle(self, center: Point, radius: float, kind: str = "visible", *, fill: str | None = None) -> None:
        layer = self._layer(kind)
        fill_attr = f'fill="{fill}"' if fill else 'fill="none"'
        if self._draws_pencil:
            n = max(20, int(2 * math.pi * radius / 1.2))
            start = self.rng.uniform(0, 2 * math.pi)
            overlap = 1.0 + min(0.1, 3.0 / max(2 * math.pi * radius, 1.0))
            pts = [
                (
                    center[0] + radius * math.cos(start + 2 * math.pi * overlap * i / n),
                    center[1] + radius * math.sin(start + 2 * math.pi * overlap * i / n),
                )
                for i in range(n + 1)
            ]
            if fill:
                self._fill_only(pts, fill, kind)
            self._pencil(pts, kind)
            return
        layer.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="{fmt(radius)}" {fill_attr} '
            f"{self._stroke_attrs(kind)}/>"
        )

    def ellipse(
        self, center: Point, rx: float, ry: float, kind: str = "visible", *, fill: str | None = None, rotate: float = 0
    ) -> None:
        """Ellipse as a closed outline, rotated clockwise on screen by `rotate` degrees."""
        theta = math.radians(rotate)
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        pts = []
        for i in range(48):
            a = 2 * math.pi * i / 48
            x, y = rx * math.cos(a), ry * math.sin(a)
            pts.append((center[0] + x * cos_t - y * sin_t, center[1] + x * sin_t + y * cos_t))
        self.polyline(pts, kind, closed=True, fill=fill)

    def curve(
        self, p0: Point, c1: Point, c2: Point, p3: Point, kind: str = "thin", *, arrow: bool = False, attrs: str = ""
    ) -> None:
        """Cubic curve, optionally with an arrowhead on `p3` that follows the curve's end direction."""
        layer = self._layer(kind)
        extra = f" {attrs}" if attrs else ""
        if self._draws_pencil:
            steps = max(6, int(math.dist(p0, p3) / 2))
            pts = []
            for i in range(steps + 1):
                t = i / steps
                u = 1 - t
                pts.append(
                    (
                        u**3 * p0[0] + 3 * u**2 * t * c1[0] + 3 * u * t**2 * c2[0] + t**3 * p3[0],
                        u**3 * p0[1] + 3 * u**2 * t * c1[1] + 3 * u * t**2 * c2[1] + t**3 * p3[1],
                    )
                )
            self._pencil(pts, kind, attrs=attrs)
        else:
            d = (
                f"M{fmt(p0[0])} {fmt(p0[1])}C{fmt(c1[0])} {fmt(c1[1])} "
                f"{fmt(c2[0])} {fmt(c2[1])} {fmt(p3[0])} {fmt(p3[1])}"
            )
            layer.append(f'<path d="{d}" {self._stroke_attrs(kind)}{extra}/>')
        if arrow:
            length = math.dist(c2, p3) or 1.0
            self.arrow_head(p3, ((p3[0] - c2[0]) / length, (p3[1] - c2[1]) / length), layer_kind=kind)

    def arc(self, center: Point, radius: float, start: float, end: float, kind: str = "visible") -> None:
        """Arc in paper space; angles in degrees, measured clockwise on screen from +x."""
        n = max(6, int(abs(end - start) / 6))
        pts = [
            (
                center[0] + radius * math.cos(math.radians(start + (end - start) * i / n)),
                center[1] + radius * math.sin(math.radians(start + (end - start) * i / n)),
            )
            for i in range(n + 1)
        ]
        self.polyline(pts, kind)

    def hatch(
        self,
        rings: Sequence[Sequence[Point]] | Sequence[Point],
        *,
        angle: float = 45,
        spacing: float = 2.5,
        kind: str = "hatch",
    ) -> None:
        """Section hatching as clipped lines. Pass one polygon, or several rings for holes (even-odd)."""
        first = rings[0]
        ring_list = [rings] if isinstance(first[0], (int, float)) else rings
        for a, b in hatch_segments(ring_list, -angle, spacing):
            if self.sketch:
                length = math.dist(a, b)
                trim = min(self.rng.uniform(0.0, 0.5), length * 0.2)
                ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
                a = (a[0] + ux * trim, a[1] + uy * trim)
                b = (b[0] - ux * self.rng.uniform(0.0, trim + 0.01), b[1] - uy * self.rng.uniform(0.0, trim + 0.01))
            self.line(a, b, kind)

    def arrow_head(
        self, tip: Point, direction: Point, *, layer_kind: str = "thin", length: float | None = None, ratio: float = 6.0
    ) -> None:
        """Arrowhead at `tip`, with `direction` the unit vector it points along."""
        length = length or self.style.arrow
        half = length / ratio
        back = (tip[0] - direction[0] * length, tip[1] - direction[1] * length)
        normal = (-direction[1], direction[0])
        left = (back[0] + normal[0] * half, back[1] + normal[1] * half)
        right = (back[0] - normal[0] * half, back[1] - normal[1] * half)
        if self.sketch:
            self.line(left, tip, layer_kind)
            self.line(right, tip, layer_kind)
            return
        coords = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in (tip, left, right))
        self._layer(layer_kind).append(f'<polygon points="{coords}" fill="{self.ink}" stroke="none"/>')

    def arrow(self, p1: Point, p2: Point, kind: str = "thin") -> None:
        length = math.dist(p1, p2)
        direction = ((p2[0] - p1[0]) / length, (p2[1] - p1[1]) / length)
        self.line(p1, p2, kind)
        self.arrow_head(p2, direction)

    def paragraph(
        self, pos: Point, text: str, width: float, size: float | str = "label", *, leading: float = 1.35, **kw: object
    ) -> float:
        """Word-wrapped text by real font metrics. Returns the y just below the last line."""
        size_mm = self.size(size)
        rows: list[str] = []
        current = ""
        for word in text.split():
            trial = f"{current} {word}".strip()
            if text_width(trial, size_mm, self.style.font) > width and current:
                rows.append(current)
                current = word
            else:
                current = trial
        if current:
            rows.append(current)
        y = pos[1]
        for row in rows:
            self.text((pos[0], y), row, size_mm, **kw)
            y += size_mm * leading
        return y

    def notes(
        self,
        x: float,
        y: float,
        items: Sequence[str],
        width: float,
        *,
        heading: str | None = None,
        size: float | str = "label",
    ) -> float:
        """Numbered notes with a hanging indent. Returns the y just below the block."""
        size_mm = self.size(size)
        if heading:
            self.text((x, y), heading, "heading")
            y += self.size("heading") * 0.6 + size_mm * 1.4
        indent = text_width("0. ", size_mm, self.style.font)
        for i, item in enumerate(items, start=1):
            self.text((x, y), f"{i}.", size_mm)
            y = self.paragraph((x + indent, y), item, width - indent, size_mm)
            y += size_mm * 0.25
        return y

    def note(
        self,
        target: Point,
        at: Point,
        lines: str | Sequence[str],
        *,
        size: float | str = "label",
        arrow: bool = True,
        knockout: bool = False,
    ) -> None:
        """Leader: arrow on `target`, oblique to `at`, short shoulder, then text beside the shoulder."""
        rows = [lines] if isinstance(lines, str) else list(lines)
        to_right = at[0] >= target[0]
        shoulder = (at[0] + (4 if to_right else -4), at[1])
        length = math.dist(target, at)
        direction = ((target[0] - at[0]) / length, (target[1] - at[1]) / length)
        self.line(at, target, "thin", attrs='data-esq-role="leader"')
        self.line(at, shoulder, "thin")
        if arrow:
            self.arrow_head(target, direction)
        size_mm = self.size(size)
        leading = size_mm * 1.3
        anchor = "start" if to_right else "end"
        x = shoulder[0] + (1 if to_right else -1)
        y = at[1] - (len(rows) - 1) * leading / 2
        for row in rows:
            self.text((x, y), row, size_mm, anchor=anchor, valign="middle", knockout=knockout)
            y += leading

    def table(
        self,
        x: float,
        y: float,
        rows: Sequence[Sequence[str]],
        col_widths: Sequence[float],
        *,
        row_height: float = 6.0,
        size: float | str = "dim",
        header: bool = True,
        align: Sequence[str] | None = None,
    ) -> Rect:
        """Grid with text fitted into each cell. Returns the table's rectangle."""
        width, height = sum(col_widths), row_height * len(rows)
        self.polyline([(x, y), (x + width, y), (x + width, y + height), (x, y + height)], "thin", closed=True)
        cx = x
        for col in col_widths[:-1]:
            cx += col
            self.line((cx, y), (cx, y + height), "thin")
        for i in range(1, len(rows)):
            self.line((x, y + i * row_height), (x + width, y + i * row_height), "thin")
        if header:
            self.line((x, y + row_height), (x + width, y + row_height), "visible", overshoot=False)
        for r, row in enumerate(rows):
            cx = x
            for c, cell in enumerate(row):
                col = col_widths[c]
                how = align[c] if align else "start"
                if how == "end":
                    pos, anchor = (cx + col - 1.2, y + (r + 0.5) * row_height), "end"
                elif how == "middle":
                    pos, anchor = (cx + col / 2, y + (r + 0.5) * row_height), "middle"
                else:
                    pos, anchor = (cx + 1.2, y + (r + 0.5) * row_height), "start"
                self.fit_text(pos, cell, col - 2.4, size, min_size=2.0, anchor=anchor, valign="middle")
                cx += col
        return (x, y, width, height)

    # ---- views and finishing --------------------------------------------------------------------

    def view(self, origin: Point, scale: Scale, *, main: bool = True) -> View:
        from .view import View

        if main and self.main_scale is None:
            self.main_scale = scale
        return View(self, origin, scale)

    def fit_view(
        self,
        world: tuple[float, float, float, float],
        *,
        area: Rect | None = None,
        pad: tuple[float, float, float, float] = (12, 12, 12, 12),
        scale: Scale | None = None,
        align: str = "center",
        main: bool = True,
    ) -> View:
        """View of `world` (xmin, ymin, xmax, ymax in real mm), scale chosen and placed by calculation.

        `pad` (left, top, right, bottom) is the paper room reserved for dimensions and notes.
        """
        x, y, w, h = area or self.area
        left, top, right, bottom = pad
        avail_w, avail_h = w - left - right, h - top - bottom
        world_w, world_h = world[2] - world[0], world[3] - world[1]
        chosen = scale or Scale.fit(world_w, world_h, avail_w, avail_h)
        if world_w * chosen.factor > avail_w + 1e-6 or world_h * chosen.factor > avail_h + 1e-6:
            raise ValueError(f"scale {chosen.label()} does not fit the area: reduce it or enlarge the sheet")
        extra_x = avail_w - world_w * chosen.factor
        extra_y = avail_h - world_h * chosen.factor
        offset_x = 0.0 if align == "start" else extra_x / 2
        offset_y = extra_y / 2
        origin = (x + left + offset_x - world[0] * chosen.factor, y + top + offset_y + world[3] * chosen.factor)
        return self.view(origin, chosen, main=main)

    def _draw_frame(self) -> None:
        if self._frame is None:
            return
        x, y, w, h = self._frame
        self._geometry.append(
            f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="none" '
            f'{self._stroke_attrs("border")} data-esq-role="frame"/>'
        )
        marks = [
            ((x + w / 2, 0.0), (x + w / 2, y)),
            ((x + w / 2, y + h), (x + w / 2, self.height)),
            ((0.0, y + h / 2), (x, y + h / 2)),
            ((x + w, y + h / 2), (self.width, y + h / 2)),
        ]
        for a, b in marks:
            self._geometry.append(
                f'<line x1="{fmt(a[0])}" y1="{fmt(a[1])}" x2="{fmt(b[0])}" y2="{fmt(b[1])}" '
                f'{self._stroke_attrs("border")} data-esq-role="centering-mark"/>'
            )

    def _projection_symbol(self, cx: float, cy: float, angle: str) -> None:
        """Truncated-cone projection symbol: the frustum's small end faces left in both methods."""
        h = 3.0
        cone_x = cx - 5.5 * h / 2 + (0 if angle == "first" else 3.2 * h)
        circle_x = cx + 5.5 * h / 2 - 1 * h if angle == "first" else cx - 5.5 * h / 2 + h
        pts = [
            (cone_x - 1.2 * h, cy - 0.5 * h),
            (cone_x + 1.2 * h, cy - h),
            (cone_x + 1.2 * h, cy + h),
            (cone_x - 1.2 * h, cy + 0.5 * h),
        ]
        keep, self.wobble = self.wobble, "none"
        self.polyline(pts, "visible", closed=True)
        self.circle((circle_x, cy), h)
        self.circle((circle_x, cy), 0.5 * h)
        self.wobble = keep
        for a, b in (
            ((cone_x - 1.9 * h, cy), (cone_x + 1.9 * h, cy)),
            ((circle_x - 1.5 * h, cy), (circle_x + 1.5 * h, cy)),
        ):
            self.line(a, b, "center", overshoot=False)
        self.line((circle_x, cy - 1.5 * h), (circle_x, cy + 1.5 * h), "center", overshoot=False)

    def _draw_title_block(self) -> None:
        block = self._title_block
        if block is None or self._frame is None:
            return
        words = STRINGS[self.lang]
        fx, fy, fw, fh = self._frame
        width = min(180.0, fw)
        height = 26.0
        x0, y0 = fx + fw - width, fy + fh - height
        symbol_w = 30.0
        row1, _row2 = 14.0, 12.0
        self.line((x0, y0), (x0 + width, y0), "visible", overshoot=False)
        self.line((x0, y0), (x0, y0 + height), "visible", overshoot=False)
        self.line((x0, y0 + row1), (x0 + width - symbol_w, y0 + row1), "thin")
        self.line((x0 + width - symbol_w, y0), (x0 + width - symbol_w, y0 + height), "thin")

        def cell(cx: float, cy: float, cw: float, label: str, value: str, size: float | str) -> None:
            self.text((cx + 1.2, cy + 3.4), label, 2.2)
            self.fit_text((cx + 1.2, cy + 3.4 + 2.2 + self.size(size) * 0.85), value, cw - 2.4, size, min_size=2.2)

        number_w = 44.0
        title_w = width - symbol_w - number_w
        cell(x0, y0, title_w, words["title"], block.get("title", ""), "heading")
        self.line((x0 + title_w, y0), (x0 + title_w, y0 + row1), "thin")
        cell(x0 + title_w, y0, number_w, words["number"], block.get("number", "—"), "label")
        scale_text = self.main_scale.label(self.lang) if self.main_scale else words["no_scale"]
        fields = [
            (28.0, words["drawn"], block.get("drawn", "—")),
            (24.0, words["date"], block.get("date", "—")),
            (30.0, words["scale"], scale_text),
            (16.0, words["size"], block.get("_size", "—")),
            (12.0, words["units"], block.get("units", "mm")),
            (10.0, words["rev"], block.get("rev", "0")),
            (30.0, words["sheet"], block.get("sheet", "1/1")),
        ]
        total = sum(f[0] for f in fields)
        room = width - symbol_w
        cx = x0
        for w, label, value in fields:
            w = w * room / total
            cell(cx, y0 + row1, w, label, value, "dim")
            cx += w
            if cx < x0 + room - 0.01:
                self.line((cx, y0 + row1), (cx, y0 + height), "thin")
        angle = block.get("projection", "first")
        if angle:
            scx, scy = x0 + width - symbol_w / 2, y0 + 10.0
            self._projection_symbol(scx, scy, angle)
            label = words["first_angle"] if angle == "first" else words["third_angle"]
            self.text((scx, y0 + height - 3.0), label, 2.5, anchor="middle")

    def _draw_scale_note(self) -> None:
        if self._title_block is not None or not self.scale_note:
            return
        words = STRINGS[self.lang]
        if self.main_scale is None or not self.main_scale.declared:
            label = words["no_scale"]
        else:
            label = f"{words['scale']} {self.main_scale.label(self.lang)}"
        self.text((self.width - 4, self.height - 4), label, "dim", anchor="end", attrs='data-esq-role="scale-note"')

    def _finish(self) -> None:
        if not self._finished:
            self._draw_frame()
            self._draw_title_block()
            self._draw_scale_note()
            self._finished = True

    def _font_face(self) -> str:
        font = self.style.font
        data = base64.b64encode((FONT_DIR / f"{font}.woff2").read_bytes()).decode("ascii")
        return (
            f"@font-face{{font-family:'{self.style.family}';"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');}}"
        )

    def to_svg(self, *, embed_font: bool = True) -> str:
        """Self-contained SVG: no external fonts, scripts or images."""
        self._finish()
        style = self.style
        defs = []
        if embed_font:
            defs.append(f"<style>{self._font_face()}</style>")
        if self._uses_wash_filter:
            defs.append(self._wash_filter())
        text_group = ""
        if self.wobble == "pencil":
            defs.append(self._grain_filter())
            defs.append(self._lettering_filter())
            text_group = f' filter="url(#{self._grain_id()}-text)"'
        scale_attr = "none" if self.scale_note else "n/a"
        if self.main_scale is not None and self.main_scale.declared:
            scale_attr = self.main_scale.label(self.lang)
        family = f"'{style.family}',{style.fallback}"
        join = "round" if self.sketch else "miter"
        common = f'fill="none" stroke="{style.ink}" stroke-linecap="{style.linecap}" stroke-linejoin="{join}"'
        title = escape(self.title_text or "Esquadro drawing")
        out = [
            (
                '<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{fmt(self.width)}mm" height="{fmt(self.height)}mm" '
                f'viewBox="0 0 {fmt(self.width)} {fmt(self.height)}" role="img" '
                f'data-esquadro="{VERSION}" data-esq-mode="{self.mode}" data-esq-scale="{scale_attr}">'
            ),
            f"<title>{title}</title>",
        ]
        if self.description:
            out.append(f"<desc>{escape(self.description)}</desc>")
        if defs:
            out.append("<defs>" + "".join(defs) + "</defs>")
        out.append(f'<rect id="esq-paper" width="{fmt(self.width)}" height="{fmt(self.height)}" fill="#fff"/>')
        out.append(f'<g id="esq-geometry" {common}>')
        out.extend(self._assemble(self._geometry))
        out.append("</g>")
        out.append(f'<g id="esq-annotations" {common}>')
        out.extend(self._assemble(self._annotations))
        out.append("</g>")
        out.append('<g id="esq-knockouts" fill="#fff" stroke="none">')
        out.extend(self._knockouts)
        out.append("</g>")
        out.append(f'<g id="esq-text" font-family="{family}" fill="{style.ink}" stroke="none"{text_group}>')
        out.extend(self._text)
        out.append("</g>")
        out.append("</svg>")
        return "\n".join(out) + "\n"

    def save(self, path: str | Path, *, embed_font: bool = True) -> Path:
        target = Path(path)
        target.write_text(self.to_svg(embed_font=embed_font), encoding="utf-8")
        return target


def bbox_of(points: Iterable[Point]) -> Rect:
    pts = list(points)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
