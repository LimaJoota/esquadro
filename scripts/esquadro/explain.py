"""Tools for explaining with a drawing: numbered callouts, hand notes, panels, free spans and emphasis.

Everything here is in paper millimetres. None of it needs real measurements, and the text in `span`
is yours to choose, so use it in figures that print "SEM ESCALA" or for rough sizes marked as such.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .core import Drawing, Point, Rect, text_width

LEADER = 'data-esq-role="leader"'


def _unit(a: Point, b: Point) -> Point:
    length = math.dist(a, b) or 1.0
    return ((b[0] - a[0]) / length, (b[1] - a[1]) / length)


def circle_points(center: Point, rx: float, ry: float | None = None) -> list[Point]:
    """Outline of a circle or ellipse, for `d.wash`."""
    ry = rx if ry is None else ry
    return [
        (center[0] + rx * math.cos(2 * math.pi * i / 40), center[1] + ry * math.sin(2 * math.pi * i / 40))
        for i in range(40)
    ]


def marker(d: Drawing, at: Point, n: int | str, *, r: float = 2.6, ink: str | None = None) -> None:
    """Number in a circle, with white behind it, so it reads on top of the drawing."""
    with d.pen(ink):
        d.circle(at, r, "thin", fill="#fff")
        d.fit_text(at, str(n), 2 * r - 1.2, r * 1.15, min_size=2.0, anchor="middle", valign="middle")


def callout(d: Drawing, target: Point, n: int | str, at: Point, *, r: float = 2.6, ink: str | None = None) -> None:
    """Numbered marker at `at` with a line to a dot on `target`. Explain the numbers with `legend`."""
    with d.pen(ink):
        ux, uy = _unit(at, target)
        d.line((at[0] + ux * r, at[1] + uy * r), target, "thin", attrs=LEADER)
        d.circle(target, 0.7, "thin", fill=d.ink)
        marker(d, at, n, r=r)


def legend(
    d: Drawing, x: float, y: float, items: Sequence[str], width: float, *, size: float | str = "label", gap: float = 1.6
) -> float:
    """Numbered explanations matching the callouts, wrapped to `width`. Returns the y below the block."""
    size_mm = d.size(size)
    r = 2.3
    indent = 2 * r + 1.8
    for i, item in enumerate(items, start=1):
        marker(d, (x + r, y + r), i, r=r)
        bottom = d.paragraph((x + indent, y + r + size_mm * 0.34), item, width - indent, size_mm)
        y = max(y + 2 * r, bottom - size_mm * 1.0) + gap
    return y


def hand_note(
    d: Drawing,
    target: Point,
    at: Point,
    text: str,
    width: float = 42.0,
    *,
    bend: float = 0.22,
    size: float | str = "label",
    ink: str | None = None,
) -> Rect:
    """Wrapped note whose top-left is `at`, with a curved arrow from its nearest side to `target`."""
    with d.pen(ink):
        return _hand_note(d, target, at, text, width, bend, size)


def _hand_note(d: Drawing, target: Point, at: Point, text: str, width: float, bend: float, size: float | str) -> Rect:
    size_mm = d.size(size)
    top = at[1]
    bottom = d.paragraph((at[0], at[1] + size_mm * 0.72), text, width, size_mm) - size_mm * 0.9
    longest = max(text_width(row, size_mm, d.style.font) for row in _wrapped(text, width, size_mm, d.style.font))
    right = at[0] + longest
    mid_y = (top + bottom) / 2
    if target[0] > right + 2:
        start = (right + 1.5, mid_y)
    elif target[0] < at[0] - 2:
        start = (at[0] - 1.5, mid_y)
    elif target[1] > bottom:
        start = ((at[0] + right) / 2, bottom + 1.5)
    else:
        start = ((at[0] + right) / 2, top - 1.5)
    dx, dy = target[0] - start[0], target[1] - start[1]
    c1 = (start[0] + dx * 0.33 - dy * bend, start[1] + dy * 0.33 + dx * bend)
    c2 = (start[0] + dx * 0.72 - dy * bend, start[1] + dy * 0.72 + dx * bend)
    d.curve(start, c1, c2, target, "thin", arrow=True, attrs=LEADER)
    return (at[0], top, right - at[0], bottom - top)


def _wrapped(text: str, width: float, size: float, font: str) -> list[str]:
    rows, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if text_width(trial, size, font) > width and current:
            rows.append(current)
            current = word
        else:
            current = trial
    return rows + ([current] if current else [])


def span(
    d: Drawing,
    a: Point,
    b: Point,
    text: str,
    *,
    side: str = "above",
    size: float | str = "dim",
    ink: str | None = None,
) -> None:
    """Double arrow with free text, such as "≈ 2 m". It measures nothing: use it for rough sizes."""
    with d.pen(ink):
        _span(d, a, b, text, side, size)


def _span(d: Drawing, a: Point, b: Point, text: str, side: str, size: float | str) -> None:
    ux, uy = _unit(a, b)
    d.line(a, b, "thin")
    d.arrow_head(a, (-ux, -uy))
    d.arrow_head(b, (ux, uy))
    angle = math.degrees(math.atan2(uy, ux))
    if angle > 90.01:
        angle -= 180
    elif angle <= -90.01:
        angle += 180
    theta = math.radians(angle)
    up = (math.sin(theta), -math.cos(theta))
    sign = 1 if side == "above" else -1
    size_mm = d.size(size)
    lift = 1.0 if side == "above" else size_mm * 0.72 + 1.0
    mid = ((a[0] + b[0]) / 2 + up[0] * lift * sign, (a[1] + b[1]) / 2 + up[1] * lift * sign)
    d.text(mid, text, size_mm, anchor="middle", rotate=angle)


def ring(d: Drawing, center: Point, rx: float, ry: float, *, turns: float = 1.12, ink: str | None = None) -> None:
    """Loose hand-drawn loop around something, the way a pen circles what matters."""
    start = d.rng.uniform(0, 2 * math.pi)
    n = 56
    pts = []
    for i in range(n + 1):
        t = i / n
        a = start + 2 * math.pi * turns * t
        grow = 1 + 0.06 * (t - 0.5)
        pts.append((center[0] + rx * grow * math.cos(a), center[1] + ry * grow * math.sin(a)))
    with d.pen(ink):
        d.polyline(pts, "visible")


def mark(d: Drawing, at: Point, ok: bool, *, size: float = 4.5, ink: str | None = None) -> None:
    """Right or wrong, as heavy strokes so it survives a black-and-white printer."""
    x, y = at
    s = size / 2
    with d.pen(ink):
        if ok:
            d.polyline([(x - s, y), (x - s * 0.25, y + s * 0.8), (x + s, y - s)], "border")
        else:
            d.line((x - s, y - s), (x + s, y + s), "border")
            d.line((x + s, y - s), (x - s, y + s), "border")


def flow_arrow(
    d: Drawing, a: Point, b: Point, *, bend: float = 0.0, label: str | None = None, ink: str | None = None
) -> None:
    """Bold arrow between steps of an explanation, straight or curved."""
    with d.pen(ink):
        _flow_arrow(d, a, b, bend, label)


def _flow_arrow(d: Drawing, a: Point, b: Point, bend: float, label: str | None) -> None:
    dx, dy = b[0] - a[0], b[1] - a[1]
    head = 3.2
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    stem_end = (b[0] - ux * head * 0.6, b[1] - uy * head * 0.6)
    c1 = (a[0] + dx * 0.33 - dy * bend, a[1] + dy * 0.33 + dx * bend)
    c2 = (a[0] + dx * 0.7 - dy * bend, a[1] + dy * 0.7 + dx * bend)
    d.curve(a, c1, c2, stem_end, "thin")
    tangent = _unit(c2, b)
    d.arrow_head(b, tangent, layer_kind="thin", length=head, ratio=2.8)
    if label:
        d.text(((a[0] + b[0]) / 2, min(a[1], b[1]) - 2.5 - abs(bend) * length * 0.5), label, "dim", anchor="middle")


@dataclass(frozen=True)
class Panel:
    """One frame of a sequence or comparison. Draw inside (x, y, w, h)."""

    x: float
    y: float
    w: float
    h: float

    def at(self, fx: float, fy: float) -> Point:
        """Point by fraction of the panel: at(0.5, 1) is the bottom centre."""
        return (self.x + self.w * fx, self.y + self.h * fy)


def panels(
    d: Drawing,
    n: int,
    *,
    area: Rect | None = None,
    titles: Sequence[str] | None = None,
    verdicts: Sequence[bool | None] | None = None,
    arrows: bool = True,
    gap: float = 14.0,
    size: float | str = "label",
    colored: bool = False,
) -> list[Panel]:
    """Split an area into a row of `n` frames with titles, arrows between them, and optional right/wrong marks.

    `colored=True` draws wrong marks in red pen and right marks in blue; their shapes still carry the meaning.
    """
    x0, y0, w, h = area or d.area
    width = (w - gap * (n - 1)) / n
    size_mm = d.size(size)
    room = width - (9.0 if verdicts else 0.0)
    lines = 0
    if titles:
        lines = max(len(_wrapped(t, room, size_mm, d.style.font)) for t in titles)
    title_h = lines * size_mm * 1.35 + 2.0 if lines else 0.0
    out = []
    for i in range(n):
        x = x0 + i * (width + gap)
        if titles:
            d.paragraph((x, y0 + size_mm * 0.75), titles[i], room, size_mm)
        if verdicts and verdicts[i] is not None:
            ink = ("blue" if verdicts[i] else "red") if colored else None
            mark(d, (x + width - 3.0, y0 + 2.4), verdicts[i], size=4.2, ink=ink)
        if arrows and i < n - 1:
            mid = y0 + title_h + (h - title_h) / 2
            flow_arrow(d, (x + width + 2.0, mid), (x + width + gap - 2.0, mid))
        out.append(Panel(x, y0 + title_h, width, h - title_h))
    return out
