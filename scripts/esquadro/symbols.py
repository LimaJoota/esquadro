"""Minimal process symbols and connections, in paper millimetres.

These follow the general look of ISA-5.1 and ISO 10628 process diagrams but are simplified and have
not been checked against those standards. See references/industrial.md.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from .core import Drawing, Point


@dataclass(frozen=True)
class Item:
    """A placed symbol: named connection ports and its bounding box (x, y, w, h)."""

    ports: dict = field(default_factory=dict)
    box: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

    def port(self, name: str) -> Point:
        return self.ports[name]


def box(d: Drawing, at: Point, w: float, h: float, lines: str | Sequence[str], *, size: float | str = "label") -> Item:
    """Labelled rectangle centred at `at`, for process steps and block diagrams."""
    x, y = at[0] - w / 2, at[1] - h / 2
    d.rect(x, y, w, h)
    rows = [lines] if isinstance(lines, str) else list(lines)
    size_mm = d.size(size)
    leading = size_mm * 1.25
    ty = at[1] - (len(rows) - 1) * leading / 2
    for row in rows:
        d.fit_text((at[0], ty), row, w - 3, size_mm, min_size=2.5, anchor="middle", valign="middle")
        ty += leading
    return Item(_side_ports(x, y, w, h), (x, y, w, h))


def _side_ports(x: float, y: float, w: float, h: float) -> dict:
    return {
        "left": (x, y + h / 2),
        "right": (x + w, y + h / 2),
        "top": (x + w / 2, y),
        "bottom": (x + w / 2, y + h),
    }


def _tag(d: Drawing, at: Point, tag: str, label: str | None, bottom: float, *, offset: float = 0.0) -> None:
    """Tag and description under a symbol; a non-zero `offset` moves them clear of a line leaving the bottom."""
    anchor = "middle" if offset == 0 else "start"
    x = at[0] + offset
    y = bottom + 3.2
    d.text((x, y), tag, "dim", anchor=anchor, valign="top")
    if label:
        d.text((x, y + 3.6), label, "dim", anchor=anchor, valign="top")


def vessel(d: Drawing, at: Point, w: float, h: float, tag: str, label: str | None = None) -> Item:
    """Vertical vessel with dished heads."""
    x, y = at[0] - w / 2, at[1] - h / 2
    head = min(w * 0.22, h * 0.2)
    n = 10
    top = [
        (at[0] - w / 2 * math.cos(math.pi * i / n), y + head - head * math.sin(math.pi * i / n)) for i in range(n + 1)
    ]
    bottom = [
        (at[0] + w / 2 * math.cos(math.pi * i / n), y + h - head + head * math.sin(math.pi * i / n))
        for i in range(n + 1)
    ]
    d.polyline(top + bottom, closed=True)
    _tag(d, at, tag, label, y + h)
    ports = _side_ports(x, y, w, h)
    ports["left_low"] = (x, y + h - head - 4)
    ports["right_low"] = (x + w, y + h - head - 4)
    ports["left_high"] = (x, y + head + 4)
    ports["right_high"] = (x + w, y + head + 4)
    return Item(ports, (x, y, w, h))


def pump(d: Drawing, at: Point, tag: str, label: str | None = None, *, r: float = 6.0) -> Item:
    """Centrifugal pump: circle with the discharge tangent at the top, suction on the left."""
    d.circle(at, r)
    x, y = at
    d.line((x, y - r), (x + r + 2.5, y - r), overshoot=False)
    _tag(d, at, tag, label, y + r)
    return Item({"in": (x - r, y), "out": (x + r + 2.5, y - r)}, (x - r, y - r, 2 * r + 2.5, 2 * r))


def valve(
    d: Drawing, at: Point, tag: str | None = None, *, size: float = 4.0, vertical: bool = False, actuator: bool = False
) -> Item:
    """Two-way valve (bowtie). `actuator=True` adds a stem and diaphragm dome, with an `actuator` port."""
    x, y = at
    s = size / 2
    pts = (
        [(x - s, y - s), (x + s, y + s), (x + s, y - s), (x - s, y + s)]
        if not vertical
        else [(x - s, y - s), (x + s, y - s), (x - s, y + s), (x + s, y + s)]
    )
    d.polyline(pts, closed=True)
    ports = {"in": (x, y - s), "out": (x, y + s)} if vertical else {"in": (x - s, y), "out": (x + s, y)}
    if actuator:
        stem_top = y - s - 3.5
        dome = 3.2
        d.line((x, y), (x, stem_top), "thin")
        d.arc((x, stem_top), dome, 180, 360, "thin")
        d.line((x - dome, stem_top), (x + dome, stem_top), "thin")
        ports["actuator"] = (x, stem_top - dome)
    if tag:
        if vertical:
            d.text((x + s + 1.2, y), tag, "dim", valign="middle")
        elif actuator:
            d.text((x, y + s + 1.5), tag, "dim", anchor="middle", valign="top")
        else:
            d.text((x, y - s - 1.5), tag, "dim", anchor="middle")
    return Item(ports, (x - s, y - s, size, size))


def exchanger(
    d: Drawing, at: Point, tag: str, label: str | None = None, *, r: float = 8.0, tag_offset: float = 0.0
) -> Item:
    """Heat exchanger: circle with a tube-side zigzag crossing it."""
    d.circle(at, r)
    x, y = at
    d.polyline(
        [
            (x - r, y),
            (x - r * 0.45, y),
            (x - r * 0.15, y - r * 0.6),
            (x + r * 0.15, y + r * 0.6),
            (x + r * 0.45, y),
            (x + r, y),
        ]
    )
    _tag(d, at, tag, label, y + r, offset=tag_offset)
    return Item(
        {"in": (x - r, y), "out": (x + r, y), "shell_in": (x, y - r), "shell_out": (x, y + r)},
        (x - r, y - r, 2 * r, 2 * r),
    )


def instrument(
    d: Drawing, at: Point, letters: str, number: str, *, location: str = "field", r: float | None = None
) -> Item:
    """Instrument bubble: function letters above the loop number. `location='panel'` adds the mid line."""
    r = r or (6.5 if d.sketch else 5.5)
    size = 3.2 if d.sketch else 2.5
    d.circle(at, r, "thin", fill="#fff")
    x, y = at
    if location == "panel":
        d.line((x - r, y), (x + r, y), "thin")
    d.fit_text((x, y - 0.8), letters, 2 * r - 2, size, min_size=2.0, anchor="middle")
    d.fit_text((x, y + size * 0.72 + 1.2), number, 2 * r - 2, size, min_size=2.0, anchor="middle")
    return Item(_side_ports(x - r, y - r, 2 * r, 2 * r), (x - r, y - r, 2 * r, 2 * r))


def pipe(
    d: Drawing,
    a: Point,
    b: Point,
    *,
    route: str = "auto",
    kind: str = "visible",
    arrow: bool = True,
    label: str | None = None,
    label_side: str = "top",
    arrow_at: float | None = None,
    label_at: float = 0.5,
) -> list[Point]:
    """Orthogonal connection between two points: 'h', 'v', 'hv', 'vh', 'hvh', 'vhv' or 'auto'."""
    if route == "auto":
        if abs(a[1] - b[1]) < 0.01:
            route = "h"
        elif abs(a[0] - b[0]) < 0.01:
            route = "v"
        else:
            route = "hvh"
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    paths = {
        "h": [a, b],
        "v": [a, b],
        "hv": [a, (b[0], a[1]), b],
        "vh": [a, (a[0], b[1]), b],
        "hvh": [a, (mx, a[1]), (mx, b[1]), b],
        "vhv": [a, (a[0], my), (b[0], my), b],
    }
    pts = paths[route]
    d.polyline(pts, kind)
    longest = max(range(len(pts) - 1), key=lambda i: math.dist(pts[i], pts[i + 1]))
    start, end = pts[longest], pts[longest + 1]
    length = math.dist(start, end)
    ux, uy = (end[0] - start[0]) / length, (end[1] - start[1]) / length
    if arrow:
        where = 0.5 if arrow_at is None else arrow_at
        size = 3.5 if kind == "visible" else 2.8
        tip = (start[0] + ux * (length * where + size / 2), start[1] + uy * (length * where + size / 2))
        d.arrow_head(tip, (ux, uy), layer_kind=kind if kind == "visible" else "thin", length=size, ratio=2.8)
    if label:
        mid = (start[0] + ux * length * label_at, start[1] + uy * length * label_at)
        if abs(ux) >= abs(uy):
            y = mid[1] - 2.0 if label_side == "top" else mid[1] + 2.0 + d.size("dim") * 0.7
            d.text((mid[0], y), label, "dim", anchor="middle")
        else:
            x = mid[0] + 2.0 if label_side != "left" else mid[0] - 2.0
            d.text((x, mid[1]), label, "dim", anchor="start" if label_side != "left" else "end", valign="middle")
    return pts
