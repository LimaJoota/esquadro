"""Explanation tools: callouts, notes, panels, isometric solids, figures and finish levels."""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest
from esquadro import (
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
from validate import validate


def errors(d: Drawing) -> list[str]:
    issues, _ = validate(d.to_svg(), browser=False)
    return [f"{i.code}: {i.message}" for i in issues if i.severity == "error"]


def test_figure_presets_match_a4_text_widths() -> None:
    assert Drawing.figure("page").width == 170.0
    assert Drawing.figure("half").width == 80.0
    assert Drawing.figure(120).width == 120.0
    assert Drawing.figure().mode == "sketch"


def test_finish_changes_the_tremor_and_unknown_is_refused() -> None:
    def scale_of(finish: str) -> float:
        return float(
            re.search(
                r'feDisplacementMap[^>]*scale="([\d.]+)"', Drawing(50, 30, "sketch", finish=finish).to_svg()
            ).group(1)
        )

    assert scale_of("napkin") > scale_of("study") > scale_of("clean")
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
    assert svg.count("<polyline") == 1  # the check is one stroke, the cross is two lines
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


@pytest.mark.parametrize("wobble", ["filter", "geometry", "none"])
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
