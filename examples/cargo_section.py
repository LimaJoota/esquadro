"""Load cross-section on a flatbed semi-trailer: pipes in a hex stack, every height computed."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, Scale, View, format_value

OUT = Path(__file__).resolve().parent

# Illustrative parameters, not a load-securing recommendation.
DECK_WIDTH = 2600.0
DECK_TOP = 1350.0
DECK_THICKNESS = 50.0
GAUGE_HEIGHT = 4400.0
PIPE_OD = 800.0
PIPE_WALL = 40.0
PIPE_MASS_T = 1.2
CHOCK = 100.0


def stack() -> list[tuple[float, float]]:
    """Pipe centres, bottom row first: each row sits in the valleys of the row below."""
    per_row = int((DECK_WIDTH - 2 * CHOCK) // PIPE_OD)
    rise = PIPE_OD * math.sqrt(3) / 2
    centres = []
    for row in range(per_row):
        count = per_row - row
        y = DECK_TOP + PIPE_OD / 2 + row * rise
        x0 = -(count - 1) * PIPE_OD / 2
        centres.extend((x0 + i * PIPE_OD, y) for i in range(count))
    return centres


def draw_section(v: View, *, sketch: bool) -> dict:
    half = DECK_WIDTH / 2
    centres = stack()
    top = max(y for _, y in centres) + PIPE_OD / 2

    # road
    v.line((-half - 300, 0), (half + 300, 0))

    # dual wheels and axle, seen from behind
    for sign in (-1, 1):
        for inner, width in ((half - 560, 270), (half - 280, 270)):
            x = sign * inner if sign > 0 else -inner - width
            v.rect(x, 0, width, 1000)
    v.rect(-half + 560, 450, DECK_WIDTH - 1120, 100, "thin")

    # chassis rails
    for x in (-550, 550):
        web, flange, depth = 12.0, 120.0, 250.0
        y0 = DECK_TOP - DECK_THICKNESS - depth
        v.polygon(
            [
                (x - flange / 2, y0),
                (x + flange / 2, y0),
                (x + flange / 2, y0 + 25),
                (x + web, y0 + 25),
                (x + web, y0 + depth - 25),
                (x + flange / 2, y0 + depth - 25),
                (x + flange / 2, y0 + depth),
                (x - flange / 2, y0 + depth),
                (x - flange / 2, y0 + depth - 25),
                (x - web, y0 + depth - 25),
                (x - web, y0 + 25),
                (x - flange / 2, y0 + 25),
            ]
        )

    # deck, cut, so hatched
    deck = [
        (-half, DECK_TOP - DECK_THICKNESS),
        (half, DECK_TOP - DECK_THICKNESS),
        (half, DECK_TOP),
        (-half, DECK_TOP),
    ]
    v.polygon(deck)
    v.hatch(deck, spacing=1.2)

    # pipes, walls cut, so hatched
    inner = PIPE_OD / 2 - PIPE_WALL
    for centre in centres:
        v.circle(centre, PIPE_OD / 2)
        v.circle(centre, inner)
        steps = 48
        ring_o = [
            (
                centre[0] + PIPE_OD / 2 * math.cos(2 * math.pi * i / steps),
                centre[1] + PIPE_OD / 2 * math.sin(2 * math.pi * i / steps),
            )
            for i in range(steps)
        ]
        ring_i = [
            (
                centre[0] + inner * math.cos(2 * math.pi * i / steps),
                centre[1] + inner * math.sin(2 * math.pi * i / steps),
            )
            for i in range(steps)
        ]
        v.hatch([ring_o, ring_i], spacing=1.0 if not sketch else 1.4)
        v.center_mark(centre)

    # chocks against the bottom row
    bottom_x = max(x for x, y in centres if abs(y - (DECK_TOP + PIPE_OD / 2)) < 1)
    for sign in (-1, 1):
        edge = sign * (bottom_x + PIPE_OD / 2)
        v.polygon(
            [
                (edge, DECK_TOP),
                (edge + sign * CHOCK, DECK_TOP),
                (edge + sign * CHOCK, DECK_TOP + 150),
                (edge + sign * 25, DECK_TOP + 150),
            ]
        )

    # reference gauge
    v.polyline([(-half, 0), (-half, GAUGE_HEIGHT), (half, GAUGE_HEIGHT), (half, 0)], "phantom")

    v.centerline((0, 0), (0, GAUGE_HEIGHT), extend=4)

    return {"centres": centres, "top": top, "bottom_x": bottom_x}


def dimension_section(v: View, info: dict) -> None:
    half = DECK_WIDTH / 2
    top = info["top"]
    v.dim_h((-half, 0), (half, 0), side="bottom", offset=9)
    v.dim_v((-half, 0), (-half, DECK_TOP), side="left", offset=9)
    v.dim_v((-half, DECK_TOP), (-half, top), side="left", offset=9)
    v.dim_v((-half, 0), (-half, GAUGE_HEIGHT), side="left", offset=19)
    v.dim_v((half, top), (half, GAUGE_HEIGHT), side="right", offset=9)
    v.dim_diameter(max(info["centres"], key=lambda c: c[1]), PIPE_OD, angle=25)


def data_rows(info: dict, lang: str = "pt") -> list[list[str]]:
    count = len(info["centres"])
    top = info["top"]
    rows = [
        ["Item", "Valor", "Origem"],
        ["Tubos no empilhamento", f"{count} un", "calculado"],
        ["Diâmetro externo", f"{format_value(PIPE_OD, lang)} mm", "parâmetro"],
        ["Altura do topo da carga", f"{format_value(top, lang)} mm", "calculado"],
        ["Folga até o gabarito", f"{format_value(GAUGE_HEIGHT - top, lang)} mm", "calculado"],
        ["Massa por tubo", f"{format_value(PIPE_MASS_T, lang, 1)} t", "parâmetro"],
        ["Massa da carga", f"{format_value(count * PIPE_MASS_T, lang, 1)} t", "calculado"],
    ]
    return rows


def technical() -> Path:
    d = Drawing.sheet(
        "A3",
        title="Corte de carga em carreta",
        description="Cross-section of a flatbed semi-trailer carrying six pipes in a hexagonal stack.",
        title_block={"number": "EX-001", "drawn": "Esquadro", "date": "2026-11-04", "rev": "0"},
    )
    area = (24.0, 12.0, 215.0, 273.0)
    world = (-DECK_WIDTH / 2, 0.0, DECK_WIDTH / 2, GAUGE_HEIGHT)
    v = d.fit_view(world, area=area, pad=(38, 9, 22, 22), scale=Scale(1, 20))
    info = draw_section(v, sketch=False)
    dimension_section(v, info)
    half = DECK_WIDTH / 2
    v.note((half - 500, GAUGE_HEIGHT), (6, -6), "Gabarito de referência")
    v.note((half, DECK_TOP - 25), (26, 14), "Plataforma")
    v.note((half - 145, 700), (31, 22), "Rodado duplo")
    v.title(0, -600, "CORTE TRANSVERSAL", with_scale=False)

    x0 = 250.0
    d.text((x0, 26), "DADOS DO ARRANJO", "heading")
    d.table(x0, 31, data_rows(info), (72, 35, 40), row_height=7, align=("start", "end", "start"))
    notes = [
        "Cotas em milímetros, geradas a partir da geometria.",
        "Tubos e calços são ilustrativos; dimensione a amarração conforme a regra de transporte aplicável.",
        "Exemplo genérico, sem valor de projeto.",
    ]
    d.notes(x0, 95, notes, 147, heading="NOTAS")
    path = d.save(OUT / "cargo_section_technical.svg")
    return path


def sketch() -> Path:
    d = Drawing(
        190,
        128,
        "sketch",
        title="Corte de carga em carreta (croqui)",
        description="Hand-style sketch of a semi-trailer section carrying six pipes.",
    )
    d.text((8, 11), "Arranjo da carga: corte", "heading")
    world = (-DECK_WIDTH / 2, 0.0, DECK_WIDTH / 2, GAUGE_HEIGHT)
    v = d.fit_view(world, area=(4.0, 14.0, 130.0, 112.0), pad=(34, 8, 30, 14), scale=Scale(1, 50))
    info = draw_section(v, sketch=True)
    dimension_section(v, info)
    half = DECK_WIDTH / 2
    v.note((half - 600, GAUGE_HEIGHT), (6, -5), "gabarito de referência")
    x0 = 136.0
    count = len(info["centres"])
    lines = [
        f"{count} tubos em 3 fiadas",
        f"topo a {format_value(info['top'])} mm",
        f"folga de {format_value(GAUGE_HEIGHT - info['top'])} mm",
        f"carga de {format_value(count * PIPE_MASS_T, 'pt', 1)} t",
    ]
    for i, row in enumerate(lines):
        d.text((x0, 60 + i * 6.5), row, "label")
    return d.save(OUT / "cargo_section_sketch.svg")


if __name__ == "__main__":
    technical()
    sketch()
