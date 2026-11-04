"""The published examples stay valid, and the deliberately bad one stays caught."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
from render import find_browser
from validate import validate

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
GOOD = sorted(p for p in EXAMPLES.glob("*.svg"))


def test_examples_exist_with_their_pictures() -> None:
    assert len(GOOD) >= 6
    for svg in GOOD:
        assert svg.with_suffix(".png").exists(), svg.name


@pytest.mark.parametrize("svg", GOOD, ids=lambda p: p.stem)
def test_example_passes_without_a_browser(svg: Path) -> None:
    issues, _ = validate(svg.read_text(encoding="utf-8"), browser=False)
    assert [i.message for i in issues if i.severity == "error"] == []


@pytest.mark.browser
@pytest.mark.skipif(find_browser() is None, reason="no browser here")
@pytest.mark.parametrize("svg", GOOD, ids=lambda p: p.stem)
def test_example_passes_with_real_text_layout(svg: Path) -> None:
    issues, summary = validate(svg.read_text(encoding="utf-8"), browser=True)
    assert summary["measured"] == "browser"
    assert [i.message for i in issues if i.severity == "error"] == []
    assert [i.code for i in issues if i.severity == "warning"] == []


def test_naive_drawing_shows_every_fault_it_was_written_with() -> None:
    raw = (EXAMPLES / "before_after" / "naive_cargo.svg").read_text(encoding="utf-8")
    issues, _ = validate(raw, browser=False)
    found = {i.code for i in issues}
    assert {"TEXT_OVERLAP", "TEXT_CROSSED", "OUT_OF_BOUNDS", "NO_SCALE"} <= found


def test_skill_quick_starts_run_and_validate(tmp_path: Path) -> None:
    root = EXAMPLES.parent
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", skill, re.DOTALL)
    assert len(blocks) >= 2
    for code in blocks:
        subprocess.run([sys.executable, "-c", code.replace("<skill>", str(root))], cwd=tmp_path, check=True)
    svgs = list(tmp_path.glob("*.svg"))
    assert len(svgs) == len(blocks)
    for svg in svgs:
        issues, _ = validate(svg.read_text(encoding="utf-8"), browser=False)
        assert [i.message for i in issues if i.severity == "error"] == []


def test_skill_frontmatter_is_well_formed() -> None:
    skill = (EXAMPLES.parent / "SKILL.md").read_text(encoding="utf-8")
    front = skill.split("---")[1]
    assert re.search(r"^name: esquadro$", front, re.MULTILINE)
    description = re.search(r"^description: (.+)$", front, re.MULTILINE).group(1)
    assert len(description) <= 1024
    assert "<" not in description


def test_versions_agree() -> None:
    from esquadro import VERSION

    skill = (EXAMPLES.parent / "SKILL.md").read_text(encoding="utf-8")
    assert f'version: "{VERSION}"' in skill
