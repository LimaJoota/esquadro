"""The validator on hand-written SVGs: each rule fires on the fault and stays quiet without it."""

from __future__ import annotations

import pytest
from render import find_browser
from validate import Document, path_points, validate

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="100mm" viewBox="0 0 200 100">'
SCALE = '<text x="150" y="95" font-size="3" font-family="Arial">SEM ESCALA</text>'


def codes(body: str, *, head: str = HEAD, scale: str = SCALE, **kw: object) -> list[str]:
    issues, _ = validate(f"{head}{body}{scale}</svg>", browser=False, **kw)
    return [i.code for i in issues if i.severity == "error"]


def warnings(body: str, *, head: str = HEAD, scale: str = SCALE) -> list[str]:
    issues, _ = validate(f"{head}{body}{scale}</svg>", browser=False)
    return [i.code for i in issues if i.severity == "warning"]


def test_clean_drawing_passes() -> None:
    body = '<text x="10" y="10" font-size="4">Label</text><line x1="10" y1="30" x2="90" y2="30" stroke="#000"/>'
    assert codes(body) == []


def test_overlapping_text_is_caught() -> None:
    body = '<text x="10" y="10" font-size="4">First label</text><text x="12" y="11" font-size="4">Second label</text>'
    assert "TEXT_OVERLAP" in codes(body)


def test_separate_lines_of_text_do_not_count_as_overlap() -> None:
    body = '<text x="10" y="10" font-size="4">First</text><text x="10" y="15" font-size="4">Second</text>'
    assert "TEXT_OVERLAP" not in codes(body)


def test_tspan_lines_are_separate_records() -> None:
    body = (
        '<text x="10" y="10" font-size="4"><tspan x="10">Line one</tspan><tspan x="10" dy="5">Line two</tspan></text>'
    )
    assert "TEXT_OVERLAP" not in codes(body)
    doc = Document(f"{HEAD}{body}</svg>")
    assert [t.content for t in doc.texts] == ["Line one", "Line two"]


def test_tspan_lines_too_close_overlap() -> None:
    body = (
        '<text x="10" y="10" font-size="4"><tspan x="10">Line one</tspan><tspan x="10" dy="1">Line two</tspan></text>'
    )
    assert "TEXT_OVERLAP" in codes(body)


def test_line_through_text_is_caught() -> None:
    body = '<text x="10" y="20" font-size="4">Crossed text</text><line x1="0" y1="19" x2="100" y2="19" stroke="#000"/>'
    assert "TEXT_CROSSED" in codes(body)


def test_line_just_under_text_is_fine() -> None:
    body = (
        '<text x="10" y="20" font-size="4">Above line</text><line x1="0" y1="21.5" x2="100" y2="21.5" stroke="#000"/>'
    )
    assert "TEXT_CROSSED" not in codes(body)


def test_text_inside_a_box_is_fine_but_overflowing_it_is_not() -> None:
    fits = '<rect x="5" y="5" width="60" height="12" fill="none" stroke="#000"/><text x="8" y="13" font-size="4">Fits</text>'
    spills = (
        '<rect x="5" y="5" width="20" height="12" fill="none" stroke="#000"/>'
        '<text x="8" y="13" font-size="4">This text spills out</text>'
    )
    assert "TEXT_CROSSED" not in codes(fits)
    assert "TEXT_CROSSED" in codes(spills)


def test_knockout_painted_between_stroke_and_text_hides_the_crossing() -> None:
    body = (
        '<line x1="0" y1="19" x2="100" y2="19" stroke="#000"/>'
        '<rect x="8" y="14" width="30" height="8" fill="#fff"/>'
        '<text x="10" y="20" font-size="4">Clear text</text>'
    )
    assert "TEXT_CROSSED" not in codes(body)


def test_stroke_painted_over_the_knockout_still_crosses() -> None:
    body = (
        '<rect x="8" y="14" width="30" height="8" fill="#fff"/>'
        '<text x="10" y="20" font-size="4">Clear text</text>'
        '<line x1="0" y1="19" x2="100" y2="19" stroke="#000"/>'
    )
    assert "TEXT_CROSSED" in codes(body)


def test_rotated_text_uses_its_real_orientation() -> None:
    upright_miss = '<text x="50" y="50" font-size="4" transform="rotate(-90 50 50)">Vertical label</text>'
    crossed = upright_miss + '<line x1="40" y1="40" x2="60" y2="40" stroke="#000"/>'
    clear = upright_miss + '<line x1="60" y1="49" x2="90" y2="49" stroke="#000"/>'
    assert "TEXT_CROSSED" in codes(crossed)
    assert "TEXT_CROSSED" not in codes(clear)


def test_group_transforms_compose() -> None:
    body = (
        '<g transform="translate(100 0)"><g transform="scale(2)">'
        '<line x1="20" y1="-5" x2="20" y2="40" stroke="#000"/></g></g>'
        '<text x="135" y="40" font-size="4">Moved here</text>'
    )
    assert "TEXT_CROSSED" in codes(body)


def test_use_expands_referenced_geometry() -> None:
    body = (
        '<defs><line id="tick" x1="0" y1="-5" x2="0" y2="5" stroke="#000"/></defs>'
        '<use href="#tick" x="20" y="20"/><text x="15" y="21" font-size="4">Label</text>'
    )
    assert "TEXT_CROSSED" in codes(body)


def test_css_classes_reach_the_text_size() -> None:
    body = (
        "<style>.big { font: 12px Arial; }</style>"
        '<text class="big" x="10" y="20">One</text><text class="big" x="10" y="24">Two</text>'
    )
    assert "TEXT_OVERLAP" in codes(body)


def test_elements_outside_the_canvas_are_caught() -> None:
    assert "OUT_OF_BOUNDS" in codes('<line x1="10" y1="10" x2="250" y2="10" stroke="#000"/>')
    assert "OUT_OF_BOUNDS" in codes('<text x="195" y="20" font-size="5">Too far right</text>')
    assert "OUT_OF_BOUNDS" in codes('<circle cx="10" cy="10" r="20" fill="none" stroke="#000"/>')


def test_viewbox_origin_is_respected() -> None:
    head = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-50 -50 100 100">'
    body = '<line x1="-40" y1="0" x2="40" y2="0" stroke="#000"/>'
    assert "OUT_OF_BOUNDS" not in codes(body, head=head, scale='<text x="-20" y="40" font-size="4">NTS</text>')


def test_margin_option_tightens_the_bounds() -> None:
    body = '<line x1="2" y1="50" x2="100" y2="50" stroke="#000"/>'
    assert "OUT_OF_BOUNDS" not in codes(body)
    assert "OUT_OF_BOUNDS" in codes(body, margin=5)


def test_clipped_shapes_are_not_out_of_bounds() -> None:
    body = '<g clip-path="url(#c)"><circle cx="10" cy="10" r="30" fill="none" stroke="#000"/></g>'
    assert "OUT_OF_BOUNDS" not in codes(body)


def test_external_references_are_errors() -> None:
    assert "EXTERNAL_REF" in codes('<image href="https://example.com/a.png" width="5" height="5"/>')
    assert "EXTERNAL_REF" in codes("<script>alert(1)</script>")
    assert "EXTERNAL_REF" in codes('<style>@import url("https://example.com/f.css");</style>')
    assert "EXTERNAL_REF" in codes('<style>@font-face{font-family:x;src:url("https://example.com/x.woff2")}</style>')
    assert "EXTERNAL_REF" not in codes("<style>@font-face{font-family:x;src:url(data:font/woff2;base64,AA)}</style>")


def test_entity_declarations_are_refused() -> None:
    with pytest.raises(ValueError):
        validate('<!DOCTYPE svg [<!ENTITY x "y">]><svg xmlns="http://www.w3.org/2000/svg"/>', browser=False)


def test_missing_scale_notice_is_an_error() -> None:
    assert "NO_SCALE" in codes('<text x="10" y="10" font-size="4">Plain</text>', scale="")
    assert "NO_SCALE" not in codes('<text x="10" y="10" font-size="4">ESCALA 1:50</text>', scale="")
    assert "NO_SCALE" not in codes('<text x="10" y="10" font-size="4">Not to scale</text>', scale="")


def test_nonstandard_scale_warns() -> None:
    assert "NONSTANDARD_SCALE" in warnings('<text x="10" y="10" font-size="4">Scale 1:37</text>', scale="")


def test_print_warnings() -> None:
    assert "SMALL_TEXT" in warnings('<text x="10" y="10" font-size="1">Tiny</text>')
    assert "LOW_CONTRAST" in warnings('<text x="10" y="10" font-size="4" fill="#ccc">Faint</text>')
    assert "THIN_STROKE" in warnings('<line x1="0" y1="50" x2="90" y2="50" stroke="#000" stroke-width="0.02"/>')
    assert "COLOR_ONLY" in warnings(
        '<line x1="0" y1="50" x2="90" y2="50" stroke="#e00000"/><line x1="0" y1="60" x2="90" y2="60" stroke="#004400"/>'
    )
    assert "FONT_NOT_EMBEDDED" in warnings('<text x="10" y="10" font-size="4" font-family="Arial">Word</text>')


def test_path_flattening_handles_every_command() -> None:
    subs = path_points("M0 0 L10 0 H20 V10 C20 20 30 20 30 10 S40 0 40 10 Q50 20 60 10 T80 10 A10 10 0 0 1 100 10 Z")
    xs = [p[0] for sub in subs for p in sub]
    assert min(xs) == 0 and max(xs) >= 100


def test_arc_stays_on_its_circle() -> None:
    sub = path_points("M0 0 A10 10 0 0 1 20 0")[0]
    for x, y in sub:
        assert abs((x - 10) ** 2 + y**2 - 100) < 1e-6


@pytest.mark.browser
@pytest.mark.skipif(find_browser() is None, reason="no browser here")
def test_browser_measurement_is_used_and_catches_overlap() -> None:
    body = (
        '<text x="10" y="10" font-size="4" font-family="Arial">First label here</text>'
        '<text x="30" y="10" font-size="4" font-family="Arial">Second</text>'
    )
    issues, summary = validate(f"{HEAD}{body}{SCALE}</svg>", browser=True)
    assert summary["measured"] == "browser"
    assert "TEXT_OVERLAP" in [i.code for i in issues]


@pytest.mark.browser
@pytest.mark.skipif(find_browser() is None, reason="no browser here")
def test_browser_measurement_is_refused_for_unsafe_svg() -> None:
    body = '<text x="10" y="10" font-size="4">Label</text><script>document.title="x"</script>'
    _, summary = validate(f"{HEAD}{body}{SCALE}</svg>", browser=True)
    assert summary["measured"] == "static"
