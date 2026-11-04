"""Cut with hand notes: why a sink trap keeps the smell out."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, flow_arrow, hand_note, mark

OUT = Path(__file__).resolve().parent

Point = tuple[float, float]


def bend(cx: float, cy: float, r: float) -> list[Point]:
    """Lower half circle, left to right."""
    return [(cx - r * math.cos(math.pi * i / 24), cy + r * math.sin(math.pi * i / 24)) for i in range(25)]


def main() -> Path:
    d = Drawing.figure(
        "page",
        92,
        title="Por que o sifão segura o cheiro",
        description="Corte de um sifão de pia: a água parada na curva fecha a passagem do cheiro vindo do esgoto.",
    )
    d.text((5, 9), "Por que o sifão segura o cheiro", "heading")

    cx, cy, mid, half = 62.0, 58.0, 12.0, 3.5
    pipe_y = 48.0
    wall_x = 142.0
    left_out, left_in = cx - mid - half, cx - mid + half
    right_in, right_out = cx + mid - half, cx + mid + half
    bowl_y = 28.0

    # sink
    d.polyline(
        [
            (20, 16),
            (25, bowl_y),
            (left_out, bowl_y),
            (left_out, cy),
            *bend(cx, cy, mid + half),
            (right_out, pipe_y + half),
            (wall_x, pipe_y + half),
        ]
    )
    d.polyline(
        [
            (104, 16),
            (99, bowl_y),
            (left_in, bowl_y),
            (left_in, cy),
            *bend(cx, cy, mid - half),
            (right_in, pipe_y - half),
            (wall_x, pipe_y - half),
        ]
    )

    # standing water, up to the lip of the outlet
    level = pipe_y + half
    water = [
        (left_out, level),
        (left_out, cy),
        *bend(cx, cy, mid + half),
        (right_out, level),
        (right_in, level),
        *reversed(bend(cx, cy, mid - half)),
        (left_in, level),
    ]
    d.hatch(water, angle=0, spacing=1.5)
    d.line((left_out, level), (left_in, level), "thin")
    d.line((right_in, level), (right_out, level), "thin")

    # wall and sewer
    d.line((wall_x, 18), (wall_x, 82))
    d.hatch([(wall_x, 18), (wall_x + 6, 18), (wall_x + 6, 82), (wall_x, 82)], spacing=2.4)

    # smell comes from the sewer and stops at the water
    flow_arrow(d, (wall_x - 3, pipe_y), (right_out + 12, pipe_y))
    mark(d, (right_out + 7, pipe_y), False, size=5)

    d.text((62, 24), "água da pia", "label", anchor="middle")
    hand_note(d, (cx, cy + mid + 1), (84, 72), "a água que fica na curva fecha a passagem", 50)
    hand_note(d, (118, pipe_y - half - 1), (106, 18), "o cheiro do esgoto para aqui", 32, bend=0.12)
    return d.save(OUT / "explain_cut.svg")


if __name__ == "__main__":
    main()
