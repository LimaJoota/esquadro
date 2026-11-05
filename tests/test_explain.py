"""Explanation tools: callouts, notes, panels, isometric solids, figures and finish levels."""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import pytest
from esquadro import (
    PENS,
    WASHES,
    Drawing,
    Figures,
    Iso,
    building,
    callout,
    document,
    flow_arrow,
    hand_note,
    legend,
    mark,
    panels,
    person,
    ring,
    span,
    truck,
)
from render import find_browser, render
from validate import validate


def errors(d: Drawing) -> list[str]:
    issues, _ = validate(d.to_svg(), browser=False)
    return [f"{i.code}: {i.message}" for i in issues if i.severity == "error"]


def test_figure_presets_match_a4_text_widths() -> None:
    assert Drawing.figure("page").width == 170.0
    assert Drawing.figure("half").width == 80.0
    assert Drawing.figure(120).width == 120.0
    assert Drawing.figure().mode == "sketch"


def test_finish_changes_the_hand_and_unknown_is_refused() -> None:
    def build(finish: str) -> str:
        d = Drawing(50, 30, "sketch", finish=finish, seed=1)
        d.line((5, 15), (45, 15))
        return d.to_svg()

    assert build("napkin") != build("clean")
    with pytest.raises(ValueError):
        Drawing(50, 30, "sketch", finish="glossy")


def test_callout_and_legend_compose_cleanly() -> None:
    d = Drawing.figure("page", 80)
    d.rect(10, 20, 40, 30)
    callout(d, (30, 35), 1, (60, 15))
    callout(d, (20, 45), 2, (60, 60))
    bottom = legend(d, 90, 15, ["Primeira explicação, longa o bastante para quebrar a linha.", "Segunda."], 70)
    assert bottom > 25
    assert errors(d) == []


def test_two_digit_callouts_fit_their_marker() -> None:
    d = Drawing.figure("page", 40)
    callout(d, (20, 20), 12, (50, 20))
    assert errors(d) == []


def test_hand_note_points_at_its_target_from_any_side() -> None:
    d = Drawing.figure("page", 100)
    d.circle((85, 50), 10)
    hand_note(d, (75, 50), (5, 45), "à esquerda do alvo", 40)
    hand_note(d, (95, 50), (125, 45), "à direita do alvo", 40)
    hand_note(d, (85, 40), (70, 12), "acima do alvo", 40)
    hand_note(d, (85, 60), (70, 80), "abaixo do alvo", 40)
    assert errors(d) == []
    assert d.to_svg().count('data-esq-role="leader"') == 4


def test_span_text_is_free_and_not_checked_as_a_dimension() -> None:
    d = Drawing.figure("page", 40)
    span(d, (20, 30), (100, 30), "≈ 2 m")
    svg = d.to_svg()
    assert "≈ 2 m" in svg and "data-esq-dim" not in svg
    assert errors(d) == []


def test_vertical_span_reads_upward() -> None:
    d = Drawing.figure("page", 80)
    span(d, (20, 70), (20, 10), "≈ 3 m")
    assert "rotate(-90" in d.to_svg()
    assert errors(d) == []


def test_panels_divide_the_area_and_leave_room_for_titles() -> None:
    d = Drawing.figure("page", 80)
    frames = panels(d, 3, area=(5, 5, 160, 70), titles=["Um", "Dois", "Três"], gap=10)
    assert len(frames) == 3
    assert math.isclose(frames[1].x - frames[0].x, frames[0].w + 10)
    assert math.isclose(frames[2].x + frames[2].w, 165)
    assert frames[0].y > 5
    assert frames[0].at(0.5, 1.0) == (frames[0].x + frames[0].w / 2, frames[0].y + frames[0].h)
    assert errors(d) == []


def test_verdicts_draw_right_and_wrong_differently() -> None:
    d = Drawing.figure("page", 60)
    panels(d, 2, area=(5, 5, 160, 50), titles=["Errado", "Certo"], verdicts=[False, True], arrows=False)
    svg = d.to_svg()
    assert svg.count("data-esq-dim") == 0
    assert errors(d) == []


def test_long_panel_titles_wrap_without_colliding() -> None:
    d = Drawing.figure("page", 80)
    panels(d, 3, area=(5, 5, 160, 70), titles=["Um título bem comprido que precisa quebrar a linha"] * 3)
    assert errors(d) == []


def test_iso_axes_run_the_right_way() -> None:
    iso = Iso(Drawing(100, 100, "sketch"), (10, 50), unit=1)
    x0, y0 = iso.p(0, 0, 0)
    xx, xy = iso.p(10, 0, 0)
    yx, yy = iso.p(0, 10, 0)
    zx, zy = iso.p(0, 0, 10)
    assert xx > x0 and xy > y0  # x: right and down
    assert yx > x0 and yy < y0  # y: right and up
    assert zx == x0 and zy == y0 - 10  # z: straight up


def test_iso_units_scale_uniformly() -> None:
    d = Drawing(100, 100, "sketch")
    a, b = Iso(d, (0, 0), unit=1), Iso(d, (0, 0), unit=2)
    assert b.p(3, 4, 5) == (a.p(3, 4, 5)[0] * 2, a.p(3, 4, 5)[1] * 2)


@pytest.mark.parametrize("axis", [(10, 0, 0), (0, 10, 0), (0, 0, 10), (6, 6, 6)])
def test_cylinder_works_in_any_direction(axis: tuple[float, float, float]) -> None:
    d = Drawing(120, 120, "sketch")
    iso = Iso(d, (50, 70), unit=2)
    info = iso.cylinder((0, 0, 0), axis, 3)
    assert set(info) == {"near", "far", "side"}
    assert errors(d) == []


def test_iso_solids_cover_what_is_behind_them() -> None:
    d = Drawing(100, 80, "sketch")
    iso = Iso(d, (20, 50), unit=1)
    iso.box(0, 0, 0, 20, 20, 20, shade="both")
    assert 'fill="#fff"' in d.to_svg()
    assert errors(d) == []


def test_objects_return_anchors_and_validate() -> None:
    d = Drawing.figure("page", 80)
    p = person(d, (15, 70), arm="out")
    doc = document(d, (40, 40))
    b = building(d, (80, 70))
    t = truck(d, (105, 70), 50)
    assert p["hand"][0] > 15
    assert doc["right"][0] > doc["left"][0]
    assert b["top"][1] < 70
    left, right, bed = t["bed"]
    assert left < right and bed < 70
    flow_arrow(d, doc["right"], b["left"])
    assert errors(d) == []


def test_truck_can_face_either_way() -> None:
    d = Drawing.figure("page", 40)
    bed_right = truck(d, (80, 30), 40, facing="right")["bed"]
    bed_left = truck(d, (80, 30), 40, facing="left")["bed"]
    assert bed_right[0] >= 80 and bed_left[1] <= 80


def test_ring_and_mark_draw_without_error() -> None:
    d = Drawing.figure("page", 40)
    ring(d, (40, 20), 10, 6)
    mark(d, (80, 20), True)
    mark(d, (100, 20), False)
    assert errors(d) == []


@pytest.mark.parametrize("wobble", ["pencil", "geometry", "none"])
def test_curves_work_in_every_wobble_mode(wobble: str) -> None:
    d = Drawing.figure("page", 60, wobble=wobble)
    hand_note(d, (120, 40), (10, 10), "nota", 30)
    flow_arrow(d, (20, 40), (60, 40), bend=0.2)
    assert errors(d) == []


def test_leader_crossing_a_dimension_warns() -> None:
    d = Drawing(120, 80, "technical")
    v = d.view((20, 40), __import__("esquadro").Scale(1, 1))
    v.dim_h((0, 0), (60, 0), side="bottom", offset=10)
    d.note((50, 60), (70, 30), "Nota")
    issues, _ = validate(d.to_svg(), browser=False)
    assert "LEADER_CROSS" in [i.code for i in issues]


def test_figures_number_in_order_of_first_use(tmp_path: Path) -> None:
    svg = tmp_path / "a.svg"
    Drawing(50, 30, "sketch", title="Exemplo", description="Texto alternativo").save(svg)
    figs = Figures()
    text = f"Veja a {figs.ref('b')} e a {figs.ref('a')}."
    html_a = figs.add("a", svg, "Legenda de a.")
    html_b = figs.add("b", svg, "Legenda de b.")
    assert text == "Veja a Figura 1 e a Figura 2."
    assert "<b>Figura 2.</b> Legenda de a." in html_a
    assert "<b>Figura 1.</b> Legenda de b." in html_b
    assert "data:image/svg+xml;base64," in html_a
    assert 'alt="Texto alternativo"' in html_a


def test_figure_caption_and_alt_are_escaped(tmp_path: Path) -> None:
    svg = tmp_path / "a.svg"
    Drawing(50, 30, "sketch", title='A "B"').save(svg)
    out = Figures("Figure").add("x", svg, "1 < 2 & 3")
    assert "1 &lt; 2 &amp; 3" in out
    assert "Figure 1" in out


def test_pen_colours_strokes_text_and_arrowheads_then_stops() -> None:
    d = Drawing(120, 60, "technical")
    with d.pen("red"):
        d.line((10, 10), (80, 10))
        d.text((10, 30), "vermelho", "label")
        d.arrow((10, 40), (50, 40))
    d.line((10, 50), (80, 50))
    svg = d.to_svg()
    red = PENS["red"]
    assert svg.count(f'stroke="{red}"') == 2
    assert f'<text x="10" y="30" font-size="3.5" fill="{red}"' in svg
    assert f'fill="{red}" stroke="none"' in svg
    assert d._pen is None
    assert 'y1="50"' in svg and f'y2="50" stroke-width="0.5" stroke="{red}"' not in svg


def test_pen_restores_after_nesting_and_after_an_error() -> None:
    d = Drawing(60, 40, "sketch")
    with d.pen("red"), d.pen("blue"):
        assert d.ink == PENS["blue"]
    assert d.ink == d.style.ink
    with pytest.raises(RuntimeError), d.pen("red"):
        raise RuntimeError
    assert d.ink == d.style.ink


def test_pen_accepts_hex_and_none() -> None:
    d = Drawing(60, 40, "sketch")
    with d.pen("#123456"):
        assert d.ink == "#123456"
    with d.pen(None):
        assert d.ink == d.style.ink


def test_red_and_blue_pens_stay_apart_in_black_and_white() -> None:
    issues, _ = validate(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><text x="1" y="49" font-size="4">NTS</text>'
        f'<line x1="0" y1="10" x2="90" y2="10" stroke="{PENS["red"]}"/>'
        f'<line x1="0" y1="20" x2="90" y2="20" stroke="{PENS["blue"]}"/></svg>',
        browser=False,
    )
    assert "COLOR_ONLY" not in [i.code for i in issues]


@pytest.mark.parametrize(
    "draw",
    [
        lambda d: callout(d, (20, 20), 1, (60, 20), ink="red"),
        lambda d: hand_note(d, (20, 20), (60, 20), "nota", 30, ink="red"),
        lambda d: span(d, (20, 30), (90, 30), "≈ 2 m", ink="red"),
        lambda d: ring(d, (40, 20), 10, 8, ink="red"),
        lambda d: mark(d, (40, 20), True, ink="red"),
        lambda d: flow_arrow(d, (20, 20), (60, 20), ink="red"),
    ],
)
def test_explaining_tools_take_an_ink(draw: Callable[[Drawing], object]) -> None:
    d = Drawing.figure("page", 50)
    draw(d)
    assert PENS["red"] in d.to_svg()
    assert errors(d) == []


def test_colored_panels_mark_wrong_red_and_right_blue() -> None:
    d = Drawing.figure("page", 60)
    panels(d, 2, area=(5, 5, 160, 50), titles=["A", "B"], verdicts=[False, True], colored=True, arrows=False)
    svg = d.to_svg()
    assert PENS["red"] in svg and PENS["blue"] in svg


def test_wash_uses_its_own_filter_and_is_not_defined_when_unused() -> None:
    assert "esq-wash" not in Drawing(60, 40, "sketch").to_svg()
    d = Drawing(60, 40, "sketch")
    d.wash([(5, 5), (30, 5), (30, 20)], "blue")
    svg = d.to_svg()
    assert svg.count("esq-wash") >= 2
    assert f'fill="{WASHES["blue"]}"' in svg and 'data-esq-role="wash"' in svg


@pytest.mark.parametrize(
    "kwargs",
    [{"wash": "flat"}, {"wobble": "geometry"}],
)
def test_flat_wash_needs_no_filter(kwargs: dict) -> None:
    d = Drawing(60, 40, "sketch", **kwargs)
    d.wash([(5, 5), (30, 5), (30, 20)], "blue")
    svg = d.to_svg()
    assert "esq-wash" not in svg and 'data-esq-role="wash"' in svg
    assert errors(d) == []


def test_unknown_wash_mode_is_refused() -> None:
    with pytest.raises(ValueError):
        Drawing(60, 40, "sketch", wash="spray")


def test_translucent_wash_does_not_hide_a_line_through_text() -> None:
    d = Drawing(120, 60, "sketch")
    d.line((5, 29), (115, 29), "visible")
    d.wash([(2, 2), (118, 2), (118, 58), (2, 58)], "blue")
    d.text((20, 30), "texto cortado", "label")
    assert any("TEXT_CROSSED" in e for e in errors(d))


def test_text_on_a_wash_edge_warns_and_inside_it_does_not() -> None:
    def codes(x: float) -> list[str]:
        d = Drawing(120, 60, "sketch")
        d.wash([(20, 10), (100, 10), (100, 50), (20, 50)], "yellow")
        d.text((x, 30), "palavra", "label")
        issues, _ = validate(d.to_svg(), browser=False)
        return [i.code for i in issues]

    assert "TEXT_ON_WASH_EDGE" not in codes(40)
    assert "TEXT_ON_WASH_EDGE" in codes(95)


def test_solids_take_a_wash() -> None:
    d = Drawing(120, 100, "sketch")
    iso = Iso(d, (20, 70), unit=1)
    iso.box(0, 0, 0, 20, 20, 20, color="yellow")
    iso.cylinder((40, 0, 0), (40, 0, 30), 8, color="blue")
    svg = d.to_svg()
    assert svg.count('data-esq-role="wash"') == 4
    assert errors(d) == []


def test_concept_figure_can_drop_the_scale_notice() -> None:
    d = Drawing.figure("page", 40, scale_note=False)
    d.text((10, 20), "Concept", "label")
    svg = d.to_svg()
    assert "NOT TO SCALE" not in svg and 'data-esq-scale="n/a"' in svg
    assert errors(d) == []


def _png_rows_with_ink(path: Path) -> list[int]:
    """Row numbers of a PNG holding anything but white, using only the standard library."""
    data = path.read_bytes()
    width, height, depth, color = struct.unpack(">IIBB", data[16:26])
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color]
    assert depth == 8
    pos, raw = 8, b""
    while pos < len(data):
        size, kind = struct.unpack(">I4s", data[pos : pos + 8])
        if kind == b"IDAT":
            raw += data[pos + 8 : pos + 8 + size]
        pos += size + 12
    pixels = zlib.decompress(raw)
    stride = width * channels
    previous = bytearray(stride)
    rows = []
    for y in range(height):
        start = y * (stride + 1)
        kind = pixels[start]
        line = bytearray(pixels[start + 1 : start + 1 + stride])
        for i in range(stride):
            a = line[i - channels] if i >= channels else 0
            b = previous[i]
            c = previous[i - channels] if i >= channels else 0
            if kind == 1:
                line[i] = (line[i] + a) & 255
            elif kind == 2:
                line[i] = (line[i] + b) & 255
            elif kind == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif kind == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        if min(line) < 128:
            rows.append(y)
        previous = line
    return rows


@pytest.mark.browser
@pytest.mark.skipif(find_browser() is None, reason="no browser here")
@pytest.mark.parametrize(
    ("dpi", "zoom"),
    [(96, None), (300, None), (500, (0, 0, 40, 20)), (96, (0, 20, 80, 20))],
)
def test_a_small_figure_is_painted_down_to_its_last_row(
    tmp_path: Path, dpi: int, zoom: tuple[float, float, float, float] | None
) -> None:
    d = Drawing.figure("half", 40, wobble="none", scale_note=False)
    d._geometry.append('<rect x="0" y="0" width="80" height="40" fill="#000" stroke="none"/>')
    png = render(d.save(tmp_path / "small.svg"), tmp_path / "small.png", dpi=dpi, zoom=zoom)
    w_mm, h_mm = zoom[2:] if zoom else (80, 40)
    width, height = struct.unpack(">II", png.read_bytes()[16:24])
    # Chrome will not scale below 0.5, so very small drawings at low dpi come out larger, never smaller.
    assert width >= w_mm * dpi / 25.4 - 2
    assert abs(width / height - w_mm / h_mm) < 0.02
    rows = _png_rows_with_ink(png)
    assert rows
    assert rows[-1] >= height - 2
