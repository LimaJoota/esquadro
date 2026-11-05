"""A non-engineering explanation: how an order becomes a delivery. People, paper, box and truck."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, Iso, building, document, flow_arrow, hand_note, person, truck

OUT = Path(__file__).resolve().parent
TEXT = {
    "pt": {
        "title": "Do pedido à entrega",
        "desc": "Cliente faz o pedido, o estoque separa, a caixa sai no caminhão e chega ao cliente.",
        "labels": ["pedido", "separação", "transporte", "entrega"],
        "paper": "o pedido é o único papel que passa por todos",
        "check": "a caixa só sai depois de conferida",
    },
    "en": {
        "title": "From order to delivery",
        "desc": "A customer orders, the warehouse picks, the box leaves by truck and reaches the customer.",
        "labels": ["order", "picking", "transport", "delivery"],
        "paper": "the order is the one paper everyone sees",
        "check": "the box leaves only after it is checked",
    },
}


def main(lang: str = "pt") -> Path:
    t = TEXT[lang]
    d = Drawing.figure("page", 84, lang=lang, title=t["title"], description=t["desc"])
    d.text((5, 9), t["title"], "heading")
    ground = 66.0
    d.line((4, ground), (166, ground), "thin")

    client = person(d, (14, ground), 24, arm="out")
    order = document(d, (37, 44), 13, 17)
    flow_arrow(d, (client["hand"][0] + 2, client["hand"][1]), (order["left"][0] - 2, order["left"][1]))

    depot = building(d, (70, ground), 34, 34)
    d.wash([(53, ground), (53, ground - 23), (70, ground - 34), (87, ground - 23), (87, ground)], "brown")
    flow_arrow(d, (order["right"][0] + 2, 44), (depot["left"][0] - 2, depot["left"][1] - 1))

    iso = Iso(d, (90, ground - 2), unit=0.42)
    iso.box(0, 0, 0, 14, 14, 12, color="yellow")

    lorry = truck(d, (104, ground), 38)
    left, right, bed = lorry["bed"]
    d.rect(left + 7, bed - 8, 12, 8, fill="#fff")
    d.wash([(left + 7, bed - 8), (left + 19, bed - 8), (left + 19, bed), (left + 7, bed)], "yellow")
    flow_arrow(d, (right + 12, ground - 8), (153, ground - 8))
    person(d, (159, ground), 24, arm="up")

    for x, label in zip((14, 70, 122, 159), t["labels"], strict=True):
        d.text((x, ground + 6), label, "label", anchor="middle")
    hand_note(d, (order["top"][0] + 2, order["top"][1] - 1), (44, 14), t["paper"], 42, bend=-0.2, ink="blue")
    hand_note(d, (left + 15, bed - 10), (102, 18), t["check"], 38, bend=0.15, ink="red")
    return d.save(OUT / f"explain_flow{'_en' if lang == 'en' else ''}.svg")


if __name__ == "__main__":
    main("pt")
    main("en")
