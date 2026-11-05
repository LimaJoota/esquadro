"""A sheet of working sketches: how many pipes fit on a truck, by diameter. Every count is computed."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, span

OUT = Path(__file__).resolve().parent

# Illustrative parameters, not a load-securing recommendation.
BAY_WIDTH = 2.5  # metres of usable deck width
BAY_HEIGHT = 2.7  # metres of usable height above the deck
PIPE_LENGTH = 6.0
DECK_LENGTH = 14.0
DIAMETERS = (1.2, 1.0, 0.8, 0.5)  # metres, outside

TEXT = {
    "pt": {
        "title": "Quantos tubos cabem na carreta",
        "desc": "Croquis de carregamento: tubos por diâmetro na seção da carreta, e a vista lateral com os trechos e o limite de altura.",
        "per_truck": "Ø {d}: {n} por carreta",
        "per_bay": "{n} em cada trecho",
        "limit": "limite de altura: {h} m acima do piso",
        "bay": "trecho {i} ({l} m)",
        "deck": "piso de {l} m: {n} trechos em linha, sobra de {s} m",
        "width": "{w} m úteis",
        "note": "contagem calculada, fileiras retas; só ilustra o método",
        "stack": "Seção: como cada diâmetro enche o trecho",
        "side": "Lateral: como os trechos ocupam a carreta",
    },
    "en": {
        "title": "How many pipes fit on the truck",
        "desc": "Loading sketches: pipes by diameter in the truck section, and the side view with the bays and height limit.",
        "per_truck": "Ø {d}: {n} per truck",
        "per_bay": "{n} in each bay",
        "limit": "height limit: {h} m above the deck",
        "bay": "bay {i} ({l} m)",
        "deck": "{l} m deck: {n} bays in a row, {s} m to spare",
        "width": "{w} m usable",
        "note": "computed count, straight rows; it only illustrates the method",
        "stack": "Section: how each diameter fills a bay",
        "side": "Side: how the bays take up the truck",
    },
}


def num(value: float, lang: str) -> str:
    out = f"{value:g}"
    return out.replace(".", ",") if lang == "pt" else out


def fit(diameter: float) -> tuple[int, int]:
    """Straight rows and columns of one diameter in the bay's section."""
    return int(BAY_WIDTH // diameter), int(BAY_HEIGHT // diameter)


def main(lang: str = "pt") -> Path:
    t = TEXT[lang]
    d = Drawing.figure("page", 128, lang=lang, title=t["title"], description=t["desc"])
    d.text((5, 8.5), t["title"], "heading")
    d.text((5, 15), t["stack"], "dim")

    bays = int(DECK_LENGTH // PIPE_LENGTH)
    box_h = 27.0
    box_w = box_h * BAY_WIDTH / BAY_HEIGHT
    gap = (160 - 4 * box_w) / 3
    for i, diameter in enumerate(DIAMETERS):
        x = 5 + i * (box_w + gap)
        y = 24.0
        cols, rows = fit(diameter)
        per_bay = cols * rows
        k = box_w / BAY_WIDTH
        d.text((x, y - 2), t["per_truck"].format(d=num(diameter, lang), n=per_bay * bays), "dim")
        d.rect(x, y, box_w, box_h)
        r = diameter * k / 2
        x0 = x + (box_w - cols * 2 * r) / 2 + r
        for row in range(rows):
            for col in range(cols):
                d.circle((x0 + col * 2 * r, y + box_h - r - row * 2 * r), r)
        d.text((x, y + box_h + 4), t["per_bay"].format(n=per_bay), "dim")

    top = 64.0
    d.text((5, top), t["side"], "dim")
    deck_y, left, k = 110.0, 13.0, 9.4
    deck_right = left + DECK_LENGTH * k
    limit_y = deck_y - BAY_HEIGHT * k
    d.line((left, limit_y), (deck_right + 5, limit_y), "phantom")
    d.text((left, limit_y - 1.6), t["limit"].format(h=num(BAY_HEIGHT, lang)), "dim")
    span(d, (deck_right + 3, deck_y), (deck_right + 3, limit_y), f"{num(BAY_HEIGHT, lang)} m")

    d.rect(left, deck_y, deck_right - left, 2.2)
    for wx in (left + 16, deck_right - 26, deck_right - 16, deck_right - 6):
        d.circle((wx, deck_y + 5.4), 3.2)
    d.polyline(
        [
            (left, deck_y),
            (left - 1, deck_y - 10),
            (left - 8, deck_y - 10),
            (left - 10, deck_y - 2),
            (left - 10, deck_y + 4),
            (left, deck_y + 4),
        ]
    )
    d.polyline(
        [(left - 2.5, deck_y - 8.5), (left - 7, deck_y - 8.5), (left - 8.4, deck_y - 3.5), (left - 2.5, deck_y - 3.5)],
        "thin",
        closed=True,
    )
    d.circle((left - 5, deck_y + 5.4), 3.2)

    diameter = DIAMETERS[1]
    cols, rows = fit(diameter)
    height = rows * diameter * k
    for bay in range(bays):
        x = left + 2.5 + bay * (PIPE_LENGTH * k + 1.5)
        w = PIPE_LENGTH * k
        d.rect(x, deck_y - height, w, height)
        for row in range(1, rows):
            ry = deck_y - row * diameter * k
            d.line((x, ry), (x + w, ry), "thin")
        d.text((x + 1.5, deck_y - height - 1.6), t["bay"].format(i=bay + 1, l=num(PIPE_LENGTH, lang)), "dim")
    used = left + 2.5 + bays * (PIPE_LENGTH * k + 1.5)
    spare = DECK_LENGTH - (used - left) / k
    span(
        d,
        (left, deck_y + 12),
        (deck_right, deck_y + 12),
        t["deck"].format(l=num(DECK_LENGTH, lang), n=bays, s=num(round(spare, 1), lang)),
        side="below",
    )
    return d.save(OUT / f"explain_load_plan{'_en' if lang == 'en' else ''}.svg")


if __name__ == "__main__":
    main("pt")
    main("en")
