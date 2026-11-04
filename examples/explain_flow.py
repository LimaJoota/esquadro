"""A non-engineering explanation: how an order becomes a delivery. People, paper, box and truck."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, Iso, building, document, flow_arrow, hand_note, person, truck

OUT = Path(__file__).resolve().parent


def main() -> Path:
    d = Drawing.figure(
        "page",
        84,
        title="Do pedido à entrega",
        description="Cliente faz o pedido, o estoque separa, a caixa sai no caminhão e chega ao cliente.",
    )
    d.text((5, 9), "Do pedido à entrega", "heading")
    ground = 66.0
    d.line((4, ground), (166, ground), "thin")

    client = person(d, (14, ground), 24, arm="out")
    order = document(d, (37, 44), 13, 17)
    flow_arrow(d, (client["hand"][0] + 2, client["hand"][1]), (order["left"][0] - 2, order["left"][1]))

    depot = building(d, (70, ground), 34, 34)
    flow_arrow(d, (order["right"][0] + 2, 44), (depot["left"][0] - 2, depot["left"][1] - 1))

    iso = Iso(d, (90, ground - 2), unit=0.42)
    iso.box(0, 0, 0, 14, 14, 12)

    lorry = truck(d, (104, ground), 38)
    left, right, bed = lorry["bed"]
    d.rect(left + 7, bed - 8, 12, 8, fill="#fff")
    flow_arrow(d, (right + 12, ground - 8), (153, ground - 8))
    person(d, (159, ground), 24, arm="up")

    d.text((14, ground + 6), "pedido", "label", anchor="middle")
    d.text((70, ground + 6), "separação", "label", anchor="middle")
    d.text((122, ground + 6), "transporte", "label", anchor="middle")
    d.text((159, ground + 6), "entrega", "label", anchor="middle")
    hand_note(
        d,
        (order["top"][0] + 2, order["top"][1] - 1),
        (44, 14),
        "o pedido é o único papel que passa por todos",
        42,
        bend=-0.2,
        size=3.8,
    )
    hand_note(d, (left + 15, bed - 10), (102, 18), "a caixa só sai depois de conferida", 38, bend=0.15, size=3.8)
    return d.save(OUT / "explain_flow.svg")


if __name__ == "__main__":
    main()
