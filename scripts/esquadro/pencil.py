"""Graphite strokes: each one is a thin filled ribbon, so width, pressure and tone can change along it.

An SVG stroke has one width and one colour from end to end, which is why it looks like a computer up
close however much it wobbles. A hand does not draw like that: pressure changes, ends taper, and a line
is often gone over twice. The paper's grain comes from a filter in `core.py`.
"""

from __future__ import annotations

import itertools
import math
import random
from collections.abc import Callable, Sequence

Point = tuple[float, float]
STEP = 1.0  # mm between samples along a stroke


def resample(pts: Sequence[Point], step: float = STEP) -> list[Point]:
    out = [pts[0]]
    for a, b in itertools.pairwise(pts):
        length = math.dist(a, b)
        n = max(1, int(length / step))
        out.extend((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1))
    return out


def _wander(rng: random.Random) -> Callable[[float], float]:
    """Smooth noise in about -1..1, as a function of distance along the stroke."""
    waves = [(rng.uniform(0.6, 1.4) * f, rng.uniform(0, 2 * math.pi)) for f in (0.35, 0.9, 2.1)]
    return lambda d: sum(math.sin(f * d + p) / (i + 1) for i, (f, p) in enumerate(waves)) / 1.8


def ribbon(
    rng: random.Random,
    pts: Sequence[Point],
    width: float,
    ink: str,
    opacity: float,
    *,
    jitter: float = 0.09,
    bow: float = 0.0,
    offset: float = 0.0,
    attrs: str = "",
) -> str:
    """One pass of the pencil along `pts`, as a closed filled path."""
    n = len(pts)
    if n < 2:
        return ""
    wobble, pressure = _wander(rng), _wander(rng)
    length = (n - 1) * STEP
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / norm, dx / norm
        d = i * STEP
        lateral = offset + wobble(d) * jitter + bow * math.sin(math.pi * i / max(n - 1, 1))
        taper = max(0.22, min(1.0, (d + 0.2) / 1.6, (length - d + 0.2) / 2.2)) ** 0.7
        half = width / 2 * (0.72 + 0.34 * pressure(d)) * taper
        cx, cy = x + nx * lateral, y + ny * lateral
        left.append((cx + nx * half, cy + ny * half))
        right.append((cx - nx * half, cy - ny * half))
    extra = f" {attrs}" if attrs else ""
    d = _smooth(left) + "L" + _smooth(right[::-1])[1:]
    return f'<path d="{d}Z" fill="{ink}" fill-opacity="{opacity:g}" stroke="none"{extra}/>'


def _smooth(pts: Sequence[Point]) -> str:
    """Path through the samples with quadratic curves, so no facets show up close."""
    out = [f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"]
    for a, b in itertools.pairwise(pts[1:]):
        out.append(f"Q{a[0]:.2f} {a[1]:.2f} {(a[0] + b[0]) / 2:.2f} {(a[1] + b[1]) / 2:.2f}")
    out.append(f"L{pts[-1][0]:.2f} {pts[-1][1]:.2f}")
    return "".join(out)


def _dashes(pts: list[Point], pattern: Sequence[float]) -> list[list[Point]]:
    """Cut a resampled path into its visible dashes."""
    out: list[list[Point]] = []
    index, left, on, travelled = 0, pattern[0], True, 0.0
    current: list[Point] = [pts[0]]
    for a, b in itertools.pairwise(pts):
        travelled = math.dist(a, b)
        if on:
            current.append(b)
        left -= travelled
        if left <= 0:
            if on and len(current) > 1:
                out.append(current)
            index = (index + 1) % len(pattern)
            left, on = pattern[index], not on
            current = [b]
    if on and len(current) > 1:
        out.append(current)
    return out


def strokes(
    rng: random.Random,
    pts: Sequence[Point],
    width: float,
    ink: str,
    opacity: float,
    *,
    dash: Sequence[float] = (),
    jitter: float = 0.09,
    bow_limit: float = 0.3,
    second_pass: float = 0.0,
    attrs: str = "",
) -> list[str]:
    """Everything one pencil line leaves on paper: its passes, and its dashes when it is dashed."""
    path = resample(pts)
    if len(path) < 2:
        return []
    length = (len(path) - 1) * STEP
    bow = rng.uniform(-1, 1) * min(bow_limit, length * 0.004)
    if dash:
        return [
            ribbon(rng, part, width, ink, opacity, jitter=jitter * 0.6, attrs=attrs) for part in _dashes(path, dash)
        ]
    out = [ribbon(rng, path, width, ink, opacity, jitter=jitter, bow=bow, attrs=attrs)]
    if length > 8 and rng.random() < second_pass:
        n = len(path)
        start = rng.uniform(0.0, 0.35)
        stop = min(1.0, start + rng.uniform(0.45, 0.7))
        part = path[int(start * (n - 1)) : int(stop * (n - 1)) + 1]
        out.append(
            ribbon(
                rng, part, width * 0.7, ink, opacity * 0.48, jitter=jitter, offset=rng.uniform(-0.13, 0.13), attrs=attrs
            )
        )
    return out
