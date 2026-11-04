#!/usr/bin/env python3
"""Regenerate every example: SVG, validate, PNG. Exits non-zero if any drawing fails validation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = (
    "explain_system.py",
    "explain_steps.py",
    "explain_compare.py",
    "explain_flow.py",
    "explain_cut.py",
    "cargo_section.py",
    "corrugated_pipe.py",
    "process_flow.py",
)
SVGS = (
    "explain_system",
    "explain_system_en",
    "explain_steps",
    "explain_steps_en",
    "explain_compare",
    "explain_compare_en",
    "explain_flow",
    "explain_flow_en",
    "explain_cut",
    "explain_cut_en",
    "cargo_section_technical",
    "cargo_section_sketch",
    "corrugated_pipe_technical",
    "corrugated_pipe_sketch",
    "process_flow_technical",
    "process_flow_sketch",
)


def main() -> int:
    for script in SCRIPTS:
        subprocess.run([sys.executable, str(HERE / script)], check=True)
    failed = 0
    for name in SVGS:
        svg = HERE / f"{name}.svg"
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), str(svg)], check=False)
        failed += result.returncode != 0
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "render.py"), str(svg), str(HERE / f"{name}.png"), "--dpi", "110"],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    naive = HERE / "before_after" / "naive_cargo.svg"
    ringed = naive.with_name("naive_cargo_annotated.svg")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate.py"), str(naive), "--annotate", str(ringed)],
        check=False,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render.py"),
            str(ringed),
            str(ringed.with_suffix(".png")),
            "--dpi",
            "120",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    ringed.unlink()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
