"""Annotated view: how a small pumping system is arranged. Volumes in perspective, numbered callouts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, Iso, callout, legend, person, ring, span

OUT = Path(__file__).resolve().parent


def main() -> Path:
    d = Drawing.figure(
        "page",
        112,
        title="Como o sistema está montado",
        description="Tanque, bomba e tubulação em perspectiva, com chamadas numeradas.",
    )
    d.text((5, 9), "Como o sistema está montado", "heading")
    iso = Iso(d, (8, 74), unit=0.62)

    iso.shadow(37, 22, 26, 22)
    iso.shadow(84, -10, 18, 16)
    # far to near
    tank = iso.cylinder((22, 34, 0), (22, 34, 56), 15)
    pipe_a = iso.cylinder((22, 18, 8), (22, -2, 8), 1.8, shade=False)
    iso.cylinder((22, -2, 8), (58, -2, 8), 1.8, shade=False)
    iso.box(58, -10, 0, 26, 16, 4, shade="right")
    pump = iso.cylinder((60, -2, 12), (78, -2, 12), 8)
    iso.cylinder((69, -2, 20), (69, -2, 42), 1.8, shade=False)
    iso.cylinder((69, -2, 42), (118, -2, 42), 1.8, shade=False)
    valve = iso.box(90, -5, 38.5, 7, 6, 7, shade="right", spacing=1.2)
    iso.cylinder((118, -2, 42), (118, -2, 6), 1.8, shade=False)
    person(d, iso.p(132, 34, 0), 21)

    callout(d, tank["side"], 1, (66, 24))
    callout(d, pipe_a["side"], 2, (11, 84))
    callout(d, pump["side"], 3, (34, 100))
    callout(d, valve["top"], 4, (82, 36))
    callout(d, iso.p(118, -2, 18), 5, (84, 100))
    ring(d, pump["side"], 13, 11)
    span(d, (17, iso.p(22, 34, 0)[1] + 3), (17, iso.p(22, 34, 56)[1] - 3), "≈ 2 m")

    legend(
        d,
        118,
        18,
        [
            "Tanque: guarda a água e mantém a bomba alimentada.",
            "Sucção: curta e sem trechos altos, para não entrar ar.",
            "Bomba: é o ponto que pede mais atenção.",
            "Válvula: regula a vazão e isola a linha na manutenção.",
            "Recalque: leva a água até o consumo.",
        ],
        50,
        size=3.8,
    )
    return d.save(OUT / "explain_system.svg")


if __name__ == "__main__":
    main()
