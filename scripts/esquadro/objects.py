"""Objects for explanatory sketches: isometric solids with hand shading, and simple people and vehicles.

All sizes are indicative. Isometric axes: x runs to the lower right, y to the upper right, z straight up.
Draw far objects first: later solids cover earlier ones.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from .core import Drawing, Point

Point3 = tuple[float, float, float]
COS30 = math.cos(math.radians(30))


def _hull(points: Sequence[Point]) -> list[Point]:
    """Convex hull, monotone chain."""
    pts = sorted(set(points))

    def turn(o: Point, a: Point, b: Point) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[Point] = []
    for p in pts:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _clip_line(origin: Point, direction: Point, rings: Sequence[Sequence[Point]]) -> list[tuple[Point, Point]]:
    """Parts of an infinite line inside the rings, even-odd."""
    ts = []
    for ring in rings:
        for a, b in zip(ring, [*ring[1:], ring[0]], strict=True):
            ex, ey = b[0] - a[0], b[1] - a[1]
            den = direction[0] * ey - direction[1] * ex
            if abs(den) < 1e-9:
                continue
            t = ((a[0] - origin[0]) * ey - (a[1] - origin[1]) * ex) / den
            u = ((a[0] - origin[0]) * direction[1] - (a[1] - origin[1]) * direction[0]) / den
            if 0 <= u < 1:
                ts.append(t)
    ts.sort()
    return [
        (
            (origin[0] + direction[0] * t1, origin[1] + direction[1] * t1),
            (origin[0] + direction[0] * t2, origin[1] + direction[1] * t2),
        )
        for t1, t2 in zip(ts[0::2], ts[1::2], strict=False)
        if t2 - t1 > 0.3
    ]


class Iso:
    """Isometric view on a drawing. `unit` is paper mm per model unit; model units are yours."""

    def __init__(self, d: Drawing, origin: Point, unit: float = 1.0) -> None:
        self.d = d
        self.origin = origin
        self.unit = unit

    def p(self, x: float, y: float, z: float = 0.0) -> Point:
        k = self.unit
        return (self.origin[0] + (x + y) * COS30 * k, self.origin[1] + ((x - y) * 0.5 - z) * k)

    def poly(
        self, pts: Sequence[Point3], *, kind: str = "visible", fill: str | None = None, closed: bool = True
    ) -> None:
        self.d.polyline([self.p(*q) for q in pts], kind, closed=closed, fill=fill)

    def line(self, a: Point3, b: Point3, kind: str = "visible") -> None:
        self.d.line(self.p(*a), self.p(*b), kind)

    def _shade(self, face: Sequence[Point3], spacing: float) -> None:
        self.d.hatch([self.p(*q) for q in face], angle=62, spacing=spacing)

    def box(
        self,
        x: float,
        y: float,
        z: float,
        w: float,
        depth: float,
        h: float,
        *,
        shade: str | None = "right",
        spacing: float = 1.8,
    ) -> dict:
        """Box from corner (x, y, z), sizes along x, y and z. `shade`: 'right', 'left', 'both' or None."""
        x2, y2, z2 = x + w, y + depth, z + h
        top = [(x, y, z2), (x2, y, z2), (x2, y2, z2), (x, y2, z2)]
        left = [(x, y, z), (x2, y, z), (x2, y, z2), (x, y, z2)]
        right = [(x2, y, z), (x2, y2, z), (x2, y2, z2), (x2, y, z2)]
        for face in (top, left, right):
            self.poly(face, fill="#fff")
        if shade in ("right", "both"):
            self._shade(right, spacing)
        if shade in ("left", "both"):
            self._shade(left, spacing * 1.7)
        return {
            "top": self.p(x + w / 2, y + depth / 2, z2),
            "left": self.p(x + w / 2, y, z + h / 2),
            "right": self.p(x2, y + depth / 2, z + h / 2),
            "base": self.p(x2, y, z),
        }

    def cylinder(self, a: Point3, b: Point3, r: float, *, shade: bool = True) -> dict:
        """Cylinder between two axis points, any direction. The end nearer the viewer shows as a full circle."""
        ax = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        norm = math.sqrt(sum(c * c for c in ax))
        ax = (ax[0] / norm, ax[1] / norm, ax[2] / norm)
        helper = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
        ux = (
            ax[1] * helper[2] - ax[2] * helper[1],
            ax[2] * helper[0] - ax[0] * helper[2],
            ax[0] * helper[1] - ax[1] * helper[0],
        )
        un = math.sqrt(sum(c * c for c in ux))
        ux = (ux[0] / un, ux[1] / un, ux[2] / un)
        vx = (ax[1] * ux[2] - ax[2] * ux[1], ax[2] * ux[0] - ax[0] * ux[2], ax[0] * ux[1] - ax[1] * ux[0])

        def ring_at(c: Point3) -> list[Point]:
            out = []
            for i in range(40):
                t = 2 * math.pi * i / 40
                cos_t, sin_t = math.cos(t) * r, math.sin(t) * r
                out.append(
                    self.p(
                        c[0] + ux[0] * cos_t + vx[0] * sin_t,
                        c[1] + ux[1] * cos_t + vx[1] * sin_t,
                        c[2] + ux[2] * cos_t + vx[2] * sin_t,
                    )
                )
            return out

        ring_a, ring_b = ring_at(a), ring_at(b)
        near_is_b = (b[0] - b[1] + b[2]) >= (a[0] - a[1] + a[2])
        near = ring_b if near_is_b else ring_a
        hull = _hull(ring_a + ring_b)
        self.d.polyline(hull, "visible", closed=True, fill="#fff")
        self.d.polyline(near, "visible", closed=True)
        pa, pb = self.p(*a), self.p(*b)
        if shade:
            length = math.dist(pa, pb) or 1.0
            axis = ((pb[0] - pa[0]) / length, (pb[1] - pa[1]) / length)
            normal = (-axis[1], axis[0])
            if normal[0] < 0:
                normal = (-normal[0], -normal[1])
            half = max((q[0] - pa[0]) * normal[0] + (q[1] - pa[1]) * normal[1] for q in hull)
            for f in (0.42, 0.6, 0.74, 0.85, 0.93):
                start = (pa[0] + normal[0] * half * f, pa[1] + normal[1] * half * f)
                for s, e in _clip_line(start, axis, [hull, near]):
                    self.d.line(s, e, "hatch")
        return {
            "near": self.p(*(b if near_is_b else a)),
            "far": self.p(*(a if near_is_b else b)),
            "side": ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2),
        }

    def shadow(self, x: float, y: float, w: float, depth: float, *, spacing: float = 1.5) -> None:
        """Hatched patch on the ground beside an object, which seats it. Draw it first."""
        face = [(x, y, 0.0), (x + w, y, 0.0), (x + w, y + depth, 0.0), (x, y + depth, 0.0)]
        self.d.hatch([self.p(*q) for q in face], angle=8, spacing=spacing)


def person(d: Drawing, feet: Point, h: float = 24.0, *, arm: str = "down") -> dict:
    """Simple standing figure. `arm`: 'down', 'up' or 'out'. Returns 'head' and 'hand' points."""
    x, y = feet
    head_r = h * 0.09
    neck = y - h + 2 * head_r
    hip = y - h * 0.47
    d.circle((x, y - h + head_r), head_r)
    d.line((x, neck), (x, hip), overshoot=False)
    d.polyline([(x - h * 0.13, y), (x, hip), (x + h * 0.13, y)])
    shoulder = neck + h * 0.07
    d.line((x, shoulder), (x - h * 0.17, shoulder + h * 0.25), overshoot=False)
    hand = {
        "down": (x + h * 0.17, shoulder + h * 0.25),
        "up": (x + h * 0.2, shoulder - h * 0.2),
        "out": (x + h * 0.3, shoulder + h * 0.02),
    }[arm]
    d.line((x, shoulder), hand, overshoot=False)
    return {"head": (x, y - h), "hand": hand}


def truck(d: Drawing, at: Point, length: float = 70.0, *, facing: str = "right") -> dict:
    """Flatbed truck in side view, `at` is the road point under the rear. Returns 'bed' (x1, x2, y) to load things on."""
    x, y = at
    k = length / 70.0
    sign = 1 if facing == "right" else -1

    def px(v: float) -> float:
        return x + sign * v * k

    wheel = 4.2 * k
    bed_y = y - 11.5 * k
    d.polygon([(px(0), bed_y), (px(50), bed_y), (px(50), bed_y + 2.5 * k), (px(0), bed_y + 2.5 * k)], fill="#fff")
    d.polyline(
        [(px(52), y - 6 * k), (px(52), y - 21 * k), (px(62), y - 21 * k), (px(69), y - 12 * k), (px(69), y - 6 * k)],
        closed=True,
        fill="#fff",
    )
    d.polyline(
        [(px(55), y - 13 * k), (px(55), y - 19 * k), (px(61), y - 19 * k), (px(65.5), y - 13 * k)], "thin", closed=True
    )
    d.line((px(50), bed_y + 2.5 * k), (px(52), bed_y + 2.5 * k), overshoot=False)
    for v in (9.0, 19.0, 60.0):
        d.circle((px(v), y - wheel), wheel, fill="#fff")
        d.circle((px(v), y - wheel), wheel * 0.35)
    left, right = sorted((px(0), px(50)))
    return {"bed": (left, right, bed_y)}


def building(d: Drawing, at: Point, w: float = 30.0, h: float = 24.0, *, door: bool = True) -> dict:
    """Simple shed with a pitched roof; `at` is the ground point at its centre."""
    x, y = at
    d.polyline(
        [(x - w / 2, y), (x - w / 2, y - h * 0.68), (x, y - h), (x + w / 2, y - h * 0.68), (x + w / 2, y)],
        closed=True,
        fill="#fff",
    )
    if door:
        d.polyline([(x - w * 0.14, y), (x - w * 0.14, y - h * 0.42), (x + w * 0.14, y - h * 0.42), (x + w * 0.14, y)])
    return {"top": (x, y - h), "left": (x - w / 2, y - h * 0.4), "right": (x + w / 2, y - h * 0.4)}


def document(d: Drawing, at: Point, w: float = 16.0, h: float = 21.0, *, lines: int = 4) -> dict:
    """Sheet with a folded corner, centred at `at`."""
    x, y = at[0] - w / 2, at[1] - h / 2
    fold = w * 0.28
    d.polyline(
        [(x, y), (x + w - fold, y), (x + w, y + fold), (x + w, y + h), (x, y + h)],
        closed=True,
        fill="#fff",
    )
    d.polyline([(x + w - fold, y), (x + w - fold, y + fold), (x + w, y + fold)], "hatch")
    step = (h - fold - 3) / max(lines, 1)
    for i in range(lines):
        ly = y + fold + 1.5 + step * i
        d.line((x + w * 0.14, ly), (x + w * 0.86, ly), "hatch")
    return {"left": (x, at[1]), "right": (x + w, at[1]), "top": (at[0], y), "bottom": (at[0], y + h)}
