"""Right and wrong, side by side: stacking pipes with and without chocks."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, circle_points, flow_arrow, hand_note, panels, ring

OUT = Path(__file__).resolve().parent
R = 9.0
TEXT = {
    "pt": {
        "title": "Calçar antes de empilhar",
        "desc": "Comparação: pilha de tubos sem calços, que rola, e com calços, que fica parada.",
        "panels": ["Sem calço: a fileira de baixo abre", "Com calço: a pilha fica travada"],
        "bad": "nada segura o tubo da ponta",
        "good": "calço dos dois lados, antes do primeiro tubo",
    },
    "en": {
        "title": "Chock before you stack",
        "desc": "Comparison: a pipe stack without chocks, which rolls, and with chocks, which stays put.",
        "panels": ["No chock: the bottom row spreads", "With chocks: the stack stays locked"],
        "bad": "nothing holds the end pipe",
        "good": "a chock on each side, before the first pipe",
    },
}


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
        d.wash(circle_points(c, R), "gray", strength=0.7)
        d.circle(c, R * 0.78, fill="#fff")
    return centres


def main(lang: str = "pt", finish: str = "study", name: str | None = None) -> Path:
    t = TEXT[lang]
    d = Drawing.figure("page", 97, finish=finish, lang=lang, title=t["title"], description=t["desc"])
    d.text((5, 9), t["title"], "heading")
    bad, good = panels(
        d,
        2,
        area=(5.0, 14.0, 160.0, 74.0),
        titles=t["panels"],
        verdicts=[False, True],
        arrows=False,
        gap=12.0,
        colored=True,
    )
    for f in (bad, good):
        y = f.y + f.h - 6
        d.line((f.x + 1, y), (f.x + f.w - 1, y))
        d.hatch([(f.x + 1, y), (f.x + f.w - 1, y), (f.x + f.w - 1, y + 3), (f.x + 1, y + 3)], spacing=2.2)

    y = bad.y + bad.h - 6
    centres = stack(d, bad.at(0.47, 0)[0], y)
    edge = max(c[0] for c in centres)
    flow_arrow(d, (edge + R + 2, y - R), (edge + R + 15, y - R), ink="red")
    ring(d, (edge, y - R), R + 2.2, R + 2.2, ink="red")
    hand_note(d, (edge + 3, y - 2 * R - 3), (bad.at(0.62, 0)[0], bad.y + 2), t["bad"], 30, bend=0.18, ink="red")

    y = good.y + good.h - 6
    cx = good.at(0.47, 0)[0]
    centres = stack(d, cx, y)
    edge = max(c[0] for c in centres) + R
    start = min(c[0] for c in centres) - R
    for chock in (
        [(edge, y), (edge + 7, y), (edge + 7, y - 7), (edge + 1.5, y - 7)],
        [(start, y), (start - 7, y), (start - 7, y - 7), (start - 1.5, y - 7)],
    ):
        d.polygon(chock, fill="#fff")
        d.wash(chock, "blue", strength=1.4)
    hand_note(d, (edge + 4, y - 7), (good.at(0.66, 0)[0], good.y + 2), t["good"], 28, bend=0.2, ink="blue")
    return d.save(OUT / f"{name or 'explain_compare' + ('_en' if lang == 'en' else '')}.svg")


if __name__ == "__main__":
    main("pt")
    main("en")
