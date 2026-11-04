"""Double-wall corrugated pipe with a socket end: half section, broken length, and a profile detail."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esquadro import Drawing, Scale, View

OUT = Path(__file__).resolve().parent

# Illustrative parameters, not a product specification.
ID = 600.0
OD = 690.0
LINER = 4.0
WALL = 3.0
PITCH = 45.0
CREST_RATIO = 0.42
FLANK = 8.0
USEFUL_LENGTH = 6000.0
SOCKET_LENGTH = 300.0
SOCKET_CLEARANCE = 6.0
SOCKET_WALL = 6.0
SHOWN_PITCHES = 16

R_IN = ID / 2
R_LINER = R_IN + LINER
R_OUT = OD / 2
R_SOCKET_IN = R_OUT + SOCKET_CLEARANCE
R_SOCKET_OUT = R_SOCKET_IN + SOCKET_WALL


def wave(x0: float, pitches: int) -> list[tuple[float, float]]:
    """Outer wall profile: valley on the liner, flank, crest at the outside diameter, flank."""
    crest = PITCH * CREST_RATIO
    valley = PITCH - crest - 2 * FLANK
    pts = [(x0, R_LINER)]
    x = x0
    for _ in range(pitches):
        pts += [
            (x + valley / 2, R_LINER),
            (x + valley / 2 + FLANK, R_OUT),
            (x + valley / 2 + FLANK + crest, R_OUT),
            (x + valley / 2 + 2 * FLANK + crest, R_LINER),
            (x + PITCH, R_LINER),
        ]
        x += PITCH
    return pts


def arches(x0: float, pitches: int) -> list[list[tuple[float, float]]]:
    """Cross-section of each corrugation: an arch of even wall thickness standing on the liner."""
    crest = PITCH * CREST_RATIO
    valley = PITCH - crest - 2 * FLANK
    shapes = []
    for i in range(pitches):
        a = x0 + i * PITCH + valley / 2
        b, c, d = a + FLANK, a + FLANK + crest, a + 2 * FLANK + crest
        shapes.append(
            [
                (a, R_LINER),
                (b, R_OUT),
                (c, R_OUT),
                (d, R_LINER),
                (d - WALL, R_LINER),
                (c - WALL * 0.8, R_OUT - WALL),
                (b + WALL * 0.8, R_OUT - WALL),
                (a + WALL, R_LINER),
            ]
        )
    return shapes


def draw_half(v: View, x_end: float) -> None:
    """Upper half cut, lower half in plain view, socket on the left, break on the right."""
    # upper half: section, thin walls in solid black as is customary at small scale
    for arch in arches(0, SHOWN_PITCHES):
        v.polyline(arch, "thin", closed=True, fill="#000")
    v.polyline([(0, R_IN), (x_end, R_IN), (x_end, R_LINER), (0, R_LINER)], "thin", closed=True, fill="#000")

    # socket, upper half
    taper = 60.0
    x_s = -SOCKET_LENGTH
    socket = [
        (x_s, R_SOCKET_OUT),
        (-taper, R_SOCKET_OUT),
        (0, R_OUT),
        (0, R_LINER),
        (-taper, R_SOCKET_IN),
        (x_s, R_SOCKET_IN),
    ]
    v.polyline(socket, "thin", closed=True, fill="#000")

    # lower half: plain outside view, one rectangle per crest
    crest = PITCH * CREST_RATIO
    valley = PITCH - crest - 2 * FLANK
    for i in range(SHOWN_PITCHES):
        x = i * PITCH + valley / 2
        v.polyline([(x, -R_LINER), (x + FLANK, -R_OUT), (x + FLANK + crest, -R_OUT), (x + 2 * FLANK + crest, -R_LINER)])
        v.line((x + FLANK, -R_OUT), (x + FLANK, 0), "thin")
        v.line((x + FLANK + crest, -R_OUT), (x + FLANK + crest, 0), "thin")
    v.line((0, -R_LINER), (SHOWN_PITCHES * PITCH, -R_LINER))
    v.polyline([(x_s, -R_SOCKET_OUT), (-taper, -R_SOCKET_OUT), (0, -R_OUT)])
    v.line((x_s, -R_SOCKET_OUT), (x_s, R_SOCKET_OUT))
    v.line((0, -R_OUT), (0, 0), "thin")
    v.line((-taper, -R_SOCKET_OUT), (-taper, 0), "thin")

    v.centerline((x_s, 0), (x_end, 0), extend=6)
    v.break_line((x_end, -R_OUT - 8), (x_end, R_OUT + 8), zigzag=3)


def dimension_half(v: View, x_end: float) -> None:
    x_s = -SOCKET_LENGTH
    v.dim_h((x_s, R_SOCKET_OUT), (0, R_SOCKET_OUT), side="top", offset=9)
    v.dim_h((0, R_OUT), (x_end, R_OUT), side="top", offset=9, value=USEFUL_LENGTH, nts=True)
    v.dim_v((x_s, -R_SOCKET_OUT), (x_s, R_SOCKET_OUT), side="left", offset=10, prefix="Ø")
    v.dim_v((x_s, -R_SOCKET_IN), (x_s, R_SOCKET_IN), side="left", offset=21, prefix="Ø")
    v.dim_v((x_end, -R_OUT), (x_end, R_OUT), side="right", offset=24, prefix="Ø")
    v.dim_v((x_end, -R_IN), (x_end, R_IN), side="right", offset=14, prefix="Ø")
    v.dim_h((3 * PITCH, -R_OUT), (4 * PITCH, -R_OUT), side="bottom", offset=9)


def draw_detail(v: View) -> None:
    """Profile at larger scale, section walls hatched."""
    pitches = 2
    for arch in arches(0, pitches):
        v.polyline(arch, closed=True)
        v.hatch(arch, spacing=1.0)
    x_end = pitches * PITCH
    liner = [(0, R_IN), (x_end, R_IN), (x_end, R_LINER), (0, R_LINER)]
    v.polygon(liner)
    v.hatch(liner, angle=-45, spacing=1.0)
    v.break_line((0, R_IN - 6), (0, R_OUT + 6), zigzag=1.5)
    v.break_line((x_end, R_IN - 6), (x_end, R_OUT + 6), zigzag=1.5)


def dimension_detail(v: View) -> None:
    crest = PITCH * CREST_RATIO
    valley = PITCH - crest - 2 * FLANK
    v.dim_h((valley / 2 + FLANK, R_OUT), (valley / 2 + FLANK + PITCH, R_OUT), side="top", offset=8)
    v.dim_v((2 * PITCH, R_IN), (2 * PITCH, R_OUT), side="right", offset=9)
    v.dim_v((0, R_IN), (0, R_LINER), side="left", offset=7)


def technical() -> Path:
    d = Drawing.sheet(
        "A3",
        lang="pt",
        title="Tubo corrugado com bolsa",
        description="Double-wall corrugated pipe with socket: half section and profile detail.",
        title_block={"number": "EX-002", "drawn": "Esquadro", "date": "2026-11-04", "rev": "0"},
    )
    x_end = SHOWN_PITCHES * PITCH
    world = (-SOCKET_LENGTH, -R_SOCKET_OUT, x_end, R_SOCKET_OUT)
    v = d.fit_view(world, area=(24.0, 14.0, 270.0, 225.0), pad=(32, 22, 32, 24), scale=Scale(1, 5))
    draw_half(v, x_end)
    dimension_half(v, x_end)
    v.note((-SOCKET_LENGTH / 2, -R_SOCKET_OUT), (-18, 14), "Bolsa")
    v.note((5 * PITCH + 20, -R_OUT), (40, 19), "Corrugação externa")
    v.title((x_end - SOCKET_LENGTH) / 2, -R_SOCKET_OUT - 150, "MEIO CORTE LONGITUDINAL")

    detail = d.fit_view(
        (0, R_IN, 2 * PITCH, R_OUT),
        area=(296.0, 18.0, 108.0, 90.0),
        pad=(4, 16, 8, 18),
        scale=Scale(1, 1),
        main=False,
    )
    draw_detail(detail)
    dimension_detail(detail)
    detail.title(PITCH, R_IN - 26, "DETALHE DO PERFIL")

    notes = [
        "Cotas em milímetros.",
        "Comprimento útil fora de escala (trecho interrompido): cota sublinhada.",
        "Paredes finas em preto no meio corte.",
        "Perfil ilustrativo; não é especificação de produto.",
    ]
    d.notes(300, 128, notes, 102, heading="NOTAS")
    return d.save(OUT / "corrugated_pipe_technical.svg")


def sketch() -> Path:
    d = Drawing(
        220,
        130,
        "sketch",
        lang="pt",
        title="Tubo corrugado com bolsa (croqui)",
        description="Hand-style sketch of a corrugated pipe with socket.",
    )
    d.text((8, 11), "Tubo corrugado com bolsa", "heading")
    x_end = 6 * PITCH
    v = d.view((75.0, 66.0), Scale.schematic(0.11))
    draw_sketch_outline(v, x_end)
    x_s = -SOCKET_LENGTH
    v.dim_h((x_s, R_SOCKET_OUT), (0, R_SOCKET_OUT), side="top", offset=8)
    v.dim_h((0, R_OUT), (x_end, R_OUT), side="top", offset=8, value=USEFUL_LENGTH, nts=True)
    v.dim_v((x_end, -R_OUT), (x_end, R_OUT), side="right", offset=21, prefix="Ø")
    v.dim_v((x_end, -R_IN), (x_end, R_IN), side="right", offset=12, prefix="Ø")
    v.note((-SOCKET_LENGTH / 2, -R_SOCKET_OUT), (-12, 12), "bolsa")
    v.note((3 * PITCH + 20, -R_OUT), (20, 11), "corrugação externa")
    return d.save(OUT / "corrugated_pipe_sketch.svg")


def draw_sketch_outline(v: View, x_end: float) -> None:
    """Plain outside view: fewer lines than the technical sheet, on purpose."""
    pitches = int(x_end // PITCH)
    crest = PITCH * CREST_RATIO
    valley = PITCH - crest - 2 * FLANK
    for sign in (1, -1):
        profile = [(x, sign * y) for x, y in wave(0, pitches)]
        v.polyline(profile)
    for i in range(pitches):
        x = i * PITCH + valley / 2
        v.line((x + FLANK, -R_OUT), (x + FLANK, R_OUT), "thin")
        v.line((x + FLANK + crest, -R_OUT), (x + FLANK + crest, R_OUT), "thin")
    x_s = -SOCKET_LENGTH
    taper = 60.0
    for sign in (1, -1):
        v.polyline([(x_s, sign * R_SOCKET_OUT), (-taper, sign * R_SOCKET_OUT), (0, sign * R_OUT)])
    v.line((x_s, -R_SOCKET_OUT), (x_s, R_SOCKET_OUT))
    v.line((-taper, -R_SOCKET_OUT), (-taper, R_SOCKET_OUT), "thin")
    v.line((0, -R_OUT), (0, R_OUT), "thin")
    v.centerline((x_s, 0), (x_end, 0), extend=5)
    v.break_line((x_end, -R_OUT - 6), (x_end, R_OUT + 6), zigzag=2.5)


if __name__ == "__main__":
    technical()
    sketch()
