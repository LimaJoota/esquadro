"""Real-world views: millimetres on the object, y up, converted to paper by a declared scale.

Dimension text is computed from the geometry being dimensioned. A value that disagrees with the
geometry is refused unless it is explicitly marked not to scale, in which case it is underlined.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence

from .core import Drawing, Point, Scale, format_value


class DimensionMismatch(ValueError):
    """A stated dimension disagrees with the drawn geometry and was not marked not to scale."""


class View:
    def __init__(self, drawing: Drawing, origin: Point, scale: Scale) -> None:
        self.d = drawing
        self.origin = origin
        self.scale = scale

    # ---- coordinates ----------------------------------------------------------------------------

    def p(self, world: Point) -> Point:
        factor = self.scale.factor
        return (self.origin[0] + world[0] * factor, self.origin[1] - world[1] * factor)

    def pts(self, world: Sequence[Point]) -> list[Point]:
        return [self.p(q) for q in world]

    # ---- geometry -------------------------------------------------------------------------------

    def line(self, a: Point, b: Point, kind: str = "visible", **kw: object) -> None:
        self.d.line(self.p(a), self.p(b), kind, **kw)

    def polyline(self, pts: Sequence[Point], kind: str = "visible", **kw: object) -> None:
        self.d.polyline(self.pts(pts), kind, **kw)

    def polygon(self, pts: Sequence[Point], kind: str = "visible", **kw: object) -> None:
        self.d.polygon(self.pts(pts), kind, **kw)

    def rect(self, x: float, y: float, w: float, h: float, kind: str = "visible", **kw: object) -> None:
        self.polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], kind, **kw)

    def circle(self, center: Point, radius: float, kind: str = "visible", **kw: object) -> None:
        self.d.circle(self.p(center), radius * self.scale.factor, kind, **kw)

    def arc(self, center: Point, radius: float, start: float, end: float, kind: str = "visible") -> None:
        """Angles in degrees, counter-clockwise from +x in world coordinates."""
        self.d.arc(self.p(center), radius * self.scale.factor, -start, -end, kind)

    def hatch(self, rings: Sequence, *, angle: float = 45, spacing: float = 2.5, kind: str = "hatch") -> None:
        """Hatch world-space polygon(s). Spacing is paper mm, so it stays legible at any scale."""
        first = rings[0]
        ring_list = [rings] if isinstance(first[0], (int, float)) else rings
        self.d.hatch([self.pts(ring) for ring in ring_list], angle=angle, spacing=spacing, kind=kind)

    def centerline(self, a: Point, b: Point, *, extend: float = 3.0) -> None:
        """Chain line running `extend` paper mm past both ends, as centre lines do."""
        pa, pb = self.p(a), self.p(b)
        length = math.dist(pa, pb)
        ux, uy = (pb[0] - pa[0]) / length, (pb[1] - pa[1]) / length
        self.d.line((pa[0] - ux * extend, pa[1] - uy * extend), (pb[0] + ux * extend, pb[1] + uy * extend), "center")

    def center_mark(self, center: Point, half: float = 2.5) -> None:
        """Small plain cross of `half` paper mm: chain dashes would not resolve at this length."""
        cx, cy = self.p(center)
        self.d.line((cx - half, cy), (cx + half, cy), "thin")
        self.d.line((cx, cy - half), (cx, cy + half), "thin")

    def break_line(self, a: Point, b: Point, *, zigzag: float = 2.0) -> None:
        """Thin ruled zigzag marking where long geometry is cut short."""
        pa, pb = self.p(a), self.p(b)
        mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
        length = math.dist(pa, pb)
        ux, uy = (pb[0] - pa[0]) / length, (pb[1] - pa[1]) / length
        nx, ny = -uy, ux
        pts = [
            (pa[0] - ux * 2, pa[1] - uy * 2),
            (mid[0] - ux * zigzag, mid[1] - uy * zigzag),
            (mid[0] - ux * zigzag * 0.5 + nx * zigzag, mid[1] - uy * zigzag * 0.5 + ny * zigzag),
            (mid[0] + ux * zigzag * 0.5 - nx * zigzag, mid[1] + uy * zigzag * 0.5 - ny * zigzag),
            (mid[0] + ux * zigzag, mid[1] + uy * zigzag),
            (pb[0] + ux * 2, pb[1] + uy * 2),
        ]
        self.d.polyline(pts, "thin")

    def section_line(self, a: Point, b: Point, letter: str, *, look: Point = (0, 1)) -> None:
        """Cutting plane: chain line, thick ends, arrows towards the viewing direction, letters."""
        pa, pb = self.p(a), self.p(b)
        self.d.line(pa, pb, "cutting")
        length = math.dist(pa, pb)
        ux, uy = (pb[0] - pa[0]) / length, (pb[1] - pa[1]) / length
        tick = 6.0
        look_paper = (look[0], -look[1])
        norm = math.hypot(*look_paper)
        look_paper = (look_paper[0] / norm, look_paper[1] / norm)
        for end, sign in ((pa, 1), (pb, -1)):
            inner = (end[0] + sign * ux * tick, end[1] + sign * uy * tick)
            self.d.line(end, inner, "visible", overshoot=False)
            tail = end
            tip = (tail[0] + look_paper[0] * 8, tail[1] + look_paper[1] * 8)
            self.d.arrow(tail, tip)
            self.d.text(
                (tip[0] + look_paper[0] * 4, tip[1] + look_paper[1] * 4),
                letter,
                "heading",
                anchor="middle",
                valign="middle",
            )

    # ---- text -----------------------------------------------------------------------------------

    def text(self, world: Point, text: str, size: float | str = "label", **kw: object) -> None:
        self.d.text(self.p(world), text, size, **kw)

    def note(self, target: Point, offset: Point, lines: str | Sequence[str], **kw: object) -> None:
        """Leader from a world point to `offset` paper mm away (x right, y down)."""
        paper = self.p(target)
        self.d.note(paper, (paper[0] + offset[0], paper[1] + offset[1]), lines, **kw)

    def title(self, x: float, y: float, text: str, *, with_scale: bool = True) -> None:
        """View caption, centred at a world point, with its own scale when it differs across the sheet."""
        label = f"{text} — {self.scale.label(self.d.lang)}" if with_scale else text
        self.d.text(self.p((x, y)), label, "label", anchor="middle")

    # ---- dimensions -----------------------------------------------------------------------------

    def dim_h(self, a: Point, b: Point, *, side: str = "bottom", offset: float = 10.0, **kw: object) -> None:
        """Horizontal dimension between two world points. `offset` is paper mm from the outermost point."""
        pa, pb = self.p(a), self.p(b)
        sign = -1 if side == "top" else 1
        y = (min(pa[1], pb[1]) if side == "top" else max(pa[1], pb[1])) + sign * offset
        first, second = (pa, pb) if pa[0] <= pb[0] else (pb, pa)
        self._dimension(first, second, (first[0], y), (second[0], y), abs(b[0] - a[0]), **kw)

    def dim_v(self, a: Point, b: Point, *, side: str = "left", offset: float = 10.0, **kw: object) -> None:
        """Vertical dimension; the value reads from the right-hand side of the sheet, as is customary."""
        pa, pb = self.p(a), self.p(b)
        sign = -1 if side == "left" else 1
        x = (min(pa[0], pb[0]) if side == "left" else max(pa[0], pb[0])) + sign * offset
        first, second = (pa, pb) if pa[1] >= pb[1] else (pb, pa)
        self._dimension(first, second, (x, first[1]), (x, second[1]), abs(b[1] - a[1]), **kw)

    def dim_aligned(self, a: Point, b: Point, *, offset: float = 10.0, **kw: object) -> None:
        """Dimension parallel to a→b. Positive offset is to the left of the travel direction on paper."""
        pa, pb = self.p(a), self.p(b)
        length = math.dist(pa, pb)
        nx, ny = (pb[1] - pa[1]) / length, -(pb[0] - pa[0]) / length
        d1 = (pa[0] + nx * offset, pa[1] + ny * offset)
        d2 = (pb[0] + nx * offset, pb[1] + ny * offset)
        self._dimension(pa, pb, d1, d2, math.dist(a, b), **kw)

    def dim_chain_h(
        self, xs: Sequence[float], y: float, *, side: str = "bottom", offset: float = 10.0, **kw: object
    ) -> None:
        """Run of horizontal dimensions sharing one dimension line."""
        for x1, x2 in itertools.pairwise(xs):
            self.dim_h((x1, y), (x2, y), side=side, offset=offset, **kw)

    def dim_diameter(self, center: Point, diameter: float, *, angle: float = 30.0, **kw: object) -> None:
        """Ø across a circle, line through the centre, value beyond the rim.

        Pass `tail` (paper mm) to carry the value clear of whatever surrounds the circle.
        """
        theta = math.radians(angle)
        half = diameter / 2
        a = (center[0] - half * math.cos(theta), center[1] - half * math.sin(theta))
        b = (center[0] + half * math.cos(theta), center[1] + half * math.sin(theta))
        pa, pb = self.p(a), self.p(b)
        kw.setdefault("prefix", "Ø")
        self._dimension(pa, pb, pa, pb, diameter, extension=False, outside=True, **kw)

    def dim_radius(self, center: Point, radius: float, *, angle: float = 45.0, **kw: object) -> None:
        """R from the centre to the rim, arrow on the rim, value past the rim."""
        theta = math.radians(angle)
        rim = (center[0] + radius * math.cos(theta), center[1] + radius * math.sin(theta))
        pc, pr = self.p(center), self.p(rim)
        kw.setdefault("prefix", "R")
        self._dimension(pc, pr, pc, pr, radius, extension=False, outside=True, single_arrow=True, **kw)

    def _dimension(
        self,
        e1: Point,
        e2: Point,
        d1: Point,
        d2: Point,
        measured: float,
        *,
        value: float | None = None,
        nts: bool = False,
        prefix: str = "",
        suffix: str = "",
        decimals: int | None = None,
        extension: bool = True,
        outside: bool = False,
        single_arrow: bool = False,
        shift: float = 0.0,
        tail: float | None = None,
    ) -> None:
        d = self.d
        shown = measured if value is None else float(value)
        tolerance = max(0.5, abs(measured) * 0.005)
        if not nts and abs(shown - measured) > tolerance:
            raise DimensionMismatch(
                f"dimension says {shown:g} but the geometry measures {measured:.1f}: fix the geometry, or pass "
                "nts=True to mark this value as not to scale"
            )
        label = f"{prefix}{format_value(shown, d.lang, decimals)}{suffix}"
        size = d.size("dim")
        text_w = d.measure(label, size)
        arrow_len = d.style.arrow

        if extension:
            gap, over = 1.0, 1.5
            for e, end in ((e1, d1), (e2, d2)):
                length = math.dist(e, end)
                if length > gap:
                    ux, uy = (end[0] - e[0]) / length, (end[1] - e[1]) / length
                    d.line((e[0] + ux * gap, e[1] + uy * gap), (end[0] + ux * over, end[1] + uy * over), "thin")

        span = math.dist(d1, d2)
        ux, uy = (d2[0] - d1[0]) / span, (d2[1] - d1[1]) / span
        angle = math.degrees(math.atan2(uy, ux))
        if angle > 90.01:
            angle -= 180
        elif angle <= -90.01:
            angle += 180
        theta = math.radians(angle)
        up = (math.sin(theta), -math.cos(theta))
        lift = 0.8

        d._dim_count += 1
        dim_id = f"esq-d{d._dim_count}"
        factor = self.scale.factor
        d.line(d1, d2, "thin", attrs=f'id="{dim_id}" data-esq-role="dimline"')

        inside = not outside and span >= text_w + 2 * arrow_len + 2
        tail = arrow_len + 4 if tail is None else tail
        if outside:
            base = d2
            d.arrow_head(d2, (ux, uy))
            if not single_arrow:
                d.arrow_head(d1, (-ux, -uy))
            shoulder_end = (d2[0] + ux * tail, d2[1] + uy * tail)
            d.line(d2, shoulder_end, "thin")
            along = tail + 1 + text_w / 2
            candidate = (base[0] + ux * along, base[1] + uy * along)
            mid_x, mid_y = candidate
        elif inside:
            d.arrow_head(d1, (-ux, -uy))
            d.arrow_head(d2, (ux, uy))
            mid_x, mid_y = (d1[0] + d2[0]) / 2 + ux * shift, (d1[1] + d2[1]) / 2 + uy * shift
        else:
            d.arrow_head(d1, (ux, uy))
            d.arrow_head(d2, (-ux, -uy))
            d.line((d1[0] - ux * tail, d1[1] - uy * tail), d1, "thin")
            d.line(d2, (d2[0] + ux * tail, d2[1] + uy * tail), "thin")
            along = tail + 1.5 + text_w / 2
            mid_x, mid_y = d2[0] + ux * along, d2[1] + uy * along

        anchor_pos = (mid_x + up[0] * lift, mid_y + up[1] * lift)
        if inside and shift == 0.0:
            anchor_pos = self._free_spot(anchor_pos, (ux, uy), label, size, angle, span, text_w, arrow_len)

        attrs = (
            f'data-esq-dim="{dim_id}" data-esq-factor="{factor:.8g}" '
            f'data-esq-value="{shown:.6g}" data-esq-nts="{1 if nts else 0}"'
        )
        d.text(anchor_pos, label, size, anchor="middle", rotate=angle, attrs=attrs)
        if nts:
            half = text_w / 2 + 0.3
            base_x, base_y = anchor_pos[0] - up[0] * 0.35, anchor_pos[1] - up[1] * 0.35
            d.line(
                (base_x - ux * half, base_y - uy * half),
                (base_x + ux * half, base_y + uy * half),
                "thin",
                attrs='data-esq-role="underline"',
            )

    def _free_spot(
        self,
        base: Point,
        along: Point,
        label: str,
        size: float,
        angle: float,
        span: float,
        text_w: float,
        arrow_len: float,
    ) -> Point:
        """Slide a dimension value along its line until it clears text that is already placed."""
        limit = max(0.0, (span - text_w) / 2 - arrow_len - 0.5)
        step = max(text_w / 2, 2.0)
        for k in range(9):
            for sign in (1, -1) if k else (1,):
                shift = sign * k * step
                if abs(shift) > limit:
                    continue
                spot = (base[0] + along[0] * shift, base[1] + along[1] * shift)
                if self.d.is_free(self.d._text_box(spot, label, size, "middle", angle)):
                    return spot
        return base
