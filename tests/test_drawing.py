"""The drawing library: scale, dimensions from geometry, hatching and self-contained output."""

from __future__ import annotations

import math
import re

import pytest
from esquadro import DimensionMismatch, Drawing, Scale, format_value, hatch_segments, text_width
from esquadro.symbols import box, exchanger, instrument, pipe, pump, valve, vessel
from validate import validate


def errors(d: Drawing) -> list[str]:
    issues, _ = validate(d.to_svg(), browser=False)
    return [f"{i.code}: {i.message}" for i in issues if i.severity == "error"]


def test_scale_fit_picks_largest_recommended_ratio() -> None:
    assert Scale.fit(1000, 500, 250, 200).label() == "1:5"
    assert Scale.fit(1000, 500, 200, 100).label() == "1:5"
    assert Scale.fit(1000, 500, 199, 100).label() == "1:10"
    assert Scale.fit(20, 10, 200, 100).label() == "10:1"


def test_scale_fit_refuses_impossible_geometry() -> None:
    with pytest.raises(ValueError):
        Scale.fit(1e9, 1, 10, 10)


def test_fit_view_refuses_a_scale_that_does_not_fit() -> None:
    d = Drawing.sheet("A4")
    with pytest.raises(ValueError):
        d.fit_view((0, 0, 10000, 1000), scale=Scale(1, 1))


def test_decimal_comma_follows_language() -> None:
    assert format_value(12.5, "pt") == "12,5"
    assert format_value(12.5, "en") == "12.5"
    assert format_value(12.0, "pt") == "12"


def test_dimension_text_comes_from_the_geometry() -> None:
    d = Drawing(200, 100, title="t")
    v = d.view((20, 50), Scale(1, 50))
    v.dim_h((0, 0), (2400, 0))
    assert ">2400</text>" in d.to_svg()


def test_dimension_that_disagrees_with_geometry_is_refused() -> None:
    d = Drawing(200, 100)
    v = d.view((20, 50), Scale(1, 50))
    with pytest.raises(DimensionMismatch):
        v.dim_h((0, 0), (2400, 0), value=3000)


def test_not_to_scale_dimension_is_underlined_and_passes() -> None:
    d = Drawing(200, 100)
    v = d.view((20, 50), Scale(1, 50))
    v.dim_h((0, 0), (2400, 0), value=6000, nts=True)
    svg = d.to_svg()
    assert 'data-esq-role="underline"' in svg
    assert errors(d) == []


def test_validator_catches_a_hand_edited_dimension() -> None:
    d = Drawing(200, 100)
    v = d.view((20, 50), Scale(1, 50))
    v.dim_h((0, 0), (2400, 0))
    tampered = d.to_svg().replace(">2400</text>", ">3100</text>")
    issues, _ = validate(tampered, browser=False)
    assert "DIM_MISMATCH" in [i.code for i in issues]


def test_validator_catches_a_removed_underline() -> None:
    d = Drawing(200, 100)
    v = d.view((20, 50), Scale(1, 50))
    v.dim_h((0, 0), (2400, 0), value=6000, nts=True)
    tampered = re.sub(r'<line[^>]*data-esq-role="underline"/>', "", d.to_svg())
    issues, _ = validate(tampered, browser=False)
    assert "DIM_NTS_MARK" in [i.code for i in issues]


def test_narrow_dimension_moves_value_outside() -> None:
    d = Drawing(200, 100)
    v = d.view((50, 50), Scale(1, 1))
    v.rect(0, 0, 4, 20)
    v.dim_h((0, 0), (4, 0), side="bottom", offset=8)
    assert errors(d) == []


def test_every_dimension_kind_validates() -> None:
    d = Drawing(240, 160, title="dims")
    v = d.view((60, 90), Scale(1, 2))
    v.rect(0, 0, 200, 100)
    v.circle((100, 50), 40)
    v.dim_h((0, 0), (200, 0), side="bottom")
    v.dim_v((0, 0), (0, 100), side="left")
    v.dim_v((200, 0), (200, 100), side="right")
    v.dim_aligned((0, 100), (200, 100), offset=8)
    v.dim_diameter((100, 50), 80, angle=30)
    assert errors(d) == []


def test_chain_shares_one_line_and_sums() -> None:
    d = Drawing(240, 80, title="chain")
    v = d.view((20, 40), Scale(1, 10))
    v.dim_chain_h([0, 600, 1500, 2000], 0)
    svg = d.to_svg()
    assert all(f">{n}</text>" in svg for n in (600, 900, 500))


def test_sheet_margins_are_iso_by_default() -> None:
    d = Drawing.sheet("A3", title="s")
    assert d._frame == (20.0, 10.0, 390.0, 277.0)
    assert 'width="420mm"' in d.to_svg()


def test_sheet_legacy_margins_for_old_brazilian_layout() -> None:
    d = Drawing.sheet("A4", "portrait", frame="nbr-1987", title="s")
    assert d._frame[0] == 25.0
    assert d.width - (d._frame[0] + d._frame[2]) == 7.0


def test_title_block_validates_on_every_size() -> None:
    for size in ("A0", "A1", "A2", "A3"):
        d = Drawing.sheet(size, title="Título", title_block={"number": "X-1"})
        assert errors(d) == [], size


def test_a4_portrait_title_block_fits() -> None:
    d = Drawing.sheet("A4", "portrait", title="Peça", title_block={"number": "X-1"})
    assert errors(d) == []


def test_title_too_long_is_refused_not_overflowed() -> None:
    d = Drawing.sheet("A3", title="x" * 300, title_block={"number": "X-1"})
    with pytest.raises(ValueError):
        d.to_svg()


def test_no_scale_notice_is_automatic() -> None:
    d = Drawing(100, 60)
    assert "SEM ESCALA" in d.to_svg()
    d = Drawing(100, 60, lang="en")
    assert "NOT TO SCALE" in d.to_svg()


def test_declared_scale_is_printed() -> None:
    d = Drawing(100, 60)
    d.view((10, 10), Scale(1, 20))
    svg = d.to_svg()
    assert "ESCALA 1:20" in svg and 'data-esq-scale="1:20"' in svg


def test_schematic_view_says_no_scale() -> None:
    d = Drawing(100, 60)
    d.view((10, 10), Scale.schematic(0.3))
    assert "SEM ESCALA" in d.to_svg()


def test_hatch_stays_inside_the_polygon() -> None:
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    segments = hatch_segments([square], 45, 1.0)
    assert segments
    for a, b in segments:
        for x, y in (a, b):
            assert -1e-6 <= x <= 10 + 1e-6 and -1e-6 <= y <= 10 + 1e-6


def test_hatch_respects_holes() -> None:
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    hole = [(4.0, 4.0), (6.0, 4.0), (6.0, 6.0), (4.0, 6.0)]
    for a, b in hatch_segments([outer, hole], 0, 0.5):
        mid_y = (a[1] + b[1]) / 2
        if 4 < mid_y < 6:
            assert not (a[0] < 5 < b[0])


@pytest.mark.parametrize("mode", ["technical", "sketch", "industrial"])
def test_output_is_self_contained(mode: str) -> None:
    d = Drawing(100, 60, mode, title="t")
    d.line((10, 10), (90, 10))
    d.text((10, 30), "Texto", "label")
    svg = d.to_svg()
    assert "<script" not in svg
    assert "http" not in svg.replace("http://www.w3.org/2000/svg", "")
    assert "base64," in svg
    assert errors(d) == []


def test_sketch_uses_the_tremor_filter_on_strokes_only() -> None:
    d = Drawing(100, 60, "sketch")
    d.line((10, 10), (90, 10))
    d.text((10, 30), "Texto", "label")
    svg = d.to_svg()
    assert "feTurbulence" in svg and "feDisplacementMap" in svg
    assert re.search(r'<g id="esq-geometry"[^>]*filter=', svg)
    assert not re.search(r'<g id="esq-text"[^>]*filter=', svg)


def test_technical_has_no_filter() -> None:
    d = Drawing(100, 60, "technical")
    d.line((10, 10), (90, 10))
    assert "<filter" not in d.to_svg()


def test_geometry_wobble_has_no_filter_and_is_reproducible() -> None:
    def build() -> str:
        d = Drawing(100, 60, "sketch", wobble="geometry", seed=3)
        d.line((10, 10), (90, 10))
        d.circle((50, 30), 10)
        return d.to_svg()

    first = build()
    assert "<filter" not in first
    assert "<path" in first
    assert first == build()


def test_filter_output_is_reproducible() -> None:
    def build(seed: int) -> str:
        d = Drawing(100, 60, "sketch", seed=seed)
        d.line((10, 10), (90, 10))
        return d.to_svg()

    assert build(4) == build(4)
    assert build(4) != build(5)


def test_text_is_escaped() -> None:
    d = Drawing(100, 60, title="A & B")
    d.text((10, 20), "x < y & z", "label")
    assert "x &lt; y &amp; z" in d.to_svg()


def test_metrics_cover_portuguese_and_drawing_symbols() -> None:
    for ch in "çãõáéíóúâêôÇÃØ±°":
        assert text_width(ch, 10, "overpass") > 0
        assert text_width(ch, 10, "patrick-hand") > 0


def test_paragraph_wraps_inside_its_width() -> None:
    d = Drawing(120, 80, title="t")
    bottom = d.paragraph((5, 10), "palavra " * 40, 60, 3.5)
    assert bottom > 20
    for x, y, w, h in d._boxes:
        assert x + w <= 65.5


@pytest.mark.parametrize("mode", ["technical", "sketch"])
def test_symbols_compose_cleanly(mode: str) -> None:
    d = Drawing(240, 120, mode, title="p")
    tank = vessel(d, (30, 50), 30, 50, "T-1", "Tanque")
    p1 = pump(d, (80, tank.port("right_low")[1]), "P-1")
    he = exchanger(d, (130, 40), "E-1")
    vv = valve(d, (170, 40), "V-1")
    step = box(d, (210, 40), 30, 16, ["Etapa", "final"])
    ti = instrument(d, (130, 12), "TI", "1")
    pipe(d, tank.port("right_low"), p1.port("in"))
    pipe(d, p1.port("out"), he.port("in"), route="hvh")
    pipe(d, he.port("out"), vv.port("in"))
    pipe(d, vv.port("out"), step.port("left"))
    pipe(d, ti.port("bottom"), he.port("shell_in"), kind="thin", arrow=False)
    assert errors(d) == []


def test_valve_actuator_has_a_port_above_the_body() -> None:
    d = Drawing(60, 40)
    item = valve(d, (30, 25), "FV-1", actuator=True)
    assert item.port("actuator")[1] < 25
    assert math.isclose(item.port("in")[1], 25)
