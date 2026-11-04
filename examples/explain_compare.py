"""Right and wrong, side by side: stacking pipes with and without chocks."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, flow_arrow, hand_note, panels, ring

OUT = Path(__file__).resolve().parent
R = 9.0


def stack(d: Drawing, cx: float, deck_y: float) -> list[tuple[float, float]]:
    """Three, two and one, each row resting in the valleys of the row below."""
    rise = 2 * R * math.sqrt(3) / 2
    centres = []
    for row, count in enumerate((3, 2, 1)):
        y = deck_y - R - row * rise
        x0 = cx - (count - 1) * R
        centres.extend((x0 + i * 2 * R, y) for i in range(count))
    for c in centres:
        d.circle(c, R, fill="#fff")
        d.circle(c, R * 0.78)
    return centres


def main(finish: str = "study", name: str = "explain_compare") -> Path:
    d = Drawing.figure(
        "page",
        92,
        finish=finish,
        title="Calçar antes de empilhar",
        description="Comparação: pilha de tubos sem calços, que rola, e com calços, que fica parada.",
    )
    d.text((5, 9), "Calçar antes de empilhar", "heading")
    bad, good = panels(
        d,
        2,
        area=(5.0, 14.0, 160.0, 74.0),
        titles=["Sem calço: a fileira de baixo abre", "Com calço: a pilha fica travada"],
        verdicts=[False, True],
        arrows=False,
        gap=12.0,
    )
    for f in (bad, good):
        y = f.y + f.h - 6
        d.line((f.x + 1, y), (f.x + f.w - 1, y))
        d.hatch([(f.x + 1, y), (f.x + f.w - 1, y), (f.x + f.w - 1, y + 3), (f.x + 1, y + 3)], spacing=2.2)

    y = bad.y + bad.h - 6
    centres = stack(d, bad.at(0.47, 0)[0], y)
    edge = max(c[0] for c in centres)
    flow_arrow(d, (edge + R + 2, y - R), (edge + R + 15, y - R), bend=0.0)
    ring(d, (edge, y - R), R + 2.2, R + 2.2)
    hand_note(
        d,
        (edge + 3, y - 2 * R - 3),
        (bad.at(0.62, 0)[0], bad.y + 2),
        "nada segura o tubo da ponta",
        30,
        bend=0.18,
        size=3.6,
    )

    y = good.y + good.h - 6
    cx = good.at(0.47, 0)[0]
    centres = stack(d, cx, y)
    edge = max(c[0] for c in centres) + R
    start = min(c[0] for c in centres) - R
    d.polygon([(edge, y), (edge + 7, y), (edge + 7, y - 7), (edge + 1.5, y - 7)], fill="#fff")
    d.polygon([(start, y), (start - 7, y), (start - 7, y - 7), (start - 1.5, y - 7)], fill="#fff")
    hand_note(
        d,
        (edge + 4, y - 7),
        (good.at(0.66, 0)[0], good.y + 2),
        "calço dos dois lados, antes do primeiro tubo",
        28,
        bend=0.2,
        size=3.6,
    )
    return d.save(OUT / f"{name}.svg")


if __name__ == "__main__":
    main()
