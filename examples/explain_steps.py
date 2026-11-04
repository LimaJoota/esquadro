"""Step sequence: assembling a socket-and-spigot pipe joint with a rubber ring, in three frames."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, circle_points, flow_arrow, hand_note, panels

OUT = Path(__file__).resolve().parent
INSERTION = 14.0  # how far the plain end goes in; the mark on the pipe sits this far from the tip
TEXT = {
    "pt": {
        "title": "Montagem da junta em três passos",
        "desc": "Sequência em três quadros: limpar e lubrificar, alinhar e encaixar até a marca.",
        "steps": ["1. Limpe e lubrifique", "2. Alinhe os dois tubos", "3. Empurre até a marca"],
        "ring": "anel limpo e assentado",
        "axis": "eixos na mesma linha",
        "stop": "marca rente à bolsa: pare",
    },
    "en": {
        "title": "Making the joint in three steps",
        "desc": "Three frames: clean and lubricate, line up, and push in to the mark.",
        "steps": ["1. Clean and lubricate", "2. Line up both pipes", "3. Push in to the mark"],
        "ring": "ring clean and seated",
        "axis": "both axes on one line",
        "stop": "mark at the socket: stop",
    },
}


def socket(d: Drawing, x: float, y: float, h: float = 26.0, length: float = 30.0) -> None:
    """Socket pipe coming in from the right, section through its wall, opening to the left."""
    t = 2.2
    half = h / 2
    d.polyline([(x, y - half - 3), (x + 13, y - half - 3), (x + 18, y - half), (x + length, y - half)])
    d.polyline([(x, y + half + 3), (x + 13, y + half + 3), (x + 18, y + half), (x + length, y + half)])
    d.polyline(
        [(x, y - half - 3 + t), (x + 13, y - half - 3 + t), (x + 17, y - half + t), (x + length, y - half + t)], "hatch"
    )
    d.polyline(
        [(x, y + half + 3 - t), (x + 13, y + half + 3 - t), (x + 17, y + half - t), (x + length, y + half - t)], "hatch"
    )
    d.line((x, y - half - 3), (x, y - half - 3 + t), overshoot=False)
    d.line((x, y + half + 3), (x, y + half + 3 - t), overshoot=False)


def spigot(d: Drawing, tip: float, y: float, h: float = 21.0, length: float = 30.0) -> None:
    """Plain pipe end, with its tip at x = tip, coming in from the left."""
    half = h / 2
    d.polyline([(tip - length, y - half), (tip, y - half), (tip, y + half), (tip - length, y + half)])
    with d.pen("blue"):
        d.line((tip - INSERTION, y - half), (tip - INSERTION, y + half), "thin")


def seal(d: Drawing, x: float, y: float) -> None:
    """The rubber ring, cut at top and bottom. It is the part this figure is about."""
    for ring_y in (y - 11.3, y + 11.3):
        d.circle((x, ring_y), 1.4, fill="#000")
        d.wash(circle_points((x, ring_y), 3.2), "red")


def main(lang: str = "pt") -> Path:
    t = TEXT[lang]
    d = Drawing.figure("page", 88, lang=lang, title=t["title"], description=t["desc"])
    d.text((5, 9), t["title"], "heading")
    frames = panels(d, 3, area=(5.0, 14.0, 160.0, 68.0), titles=t["steps"], gap=10.0)

    f = frames[0]
    y = f.at(0, 0.5)[1] + 2
    socket(d, f.x + 6, y, length=36)
    seal(d, f.x + 12, y)
    hand_note(d, (f.x + 12, y - 12.8), (f.x, f.y + 2), t["ring"], 40, bend=0.1, size=3.6, ink="red")

    f = frames[1]
    y = f.at(0, 0.5)[1] + 2
    socket(d, f.x + 22, y, length=20)
    spigot(d, f.x + 16, y, length=16)
    seal(d, f.x + 28, y)
    d.line((f.x, y), (f.x + f.w - 3, y), "center")
    hand_note(d, (f.x + 16, y + 11), (f.x, f.y + f.h - 8), t["axis"], 40, bend=-0.15, size=3.6)

    f = frames[2]
    y = f.at(0, 0.5)[1] + 2
    socket(d, f.x + 18, y, length=26)
    spigot(d, f.x + 18 + INSERTION, y, length=18 + INSERTION)
    seal(d, f.x + 24, y)
    flow_arrow(d, (f.x, y - 19), (f.x + 13, y - 19), ink="red")
    hand_note(d, (f.x + 18, y + 10.5), (f.x + 2, f.y + f.h - 8), t["stop"], 42, bend=0.15, size=3.6, ink="blue")
    return d.save(OUT / f"explain_steps{'_en' if lang == 'en' else ''}.svg")


if __name__ == "__main__":
    main("pt")
    main("en")
