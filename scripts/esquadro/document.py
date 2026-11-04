"""Figures for technical documents: numbered captions and cross-references, in self-contained HTML."""

from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path


class Figures:
    """Numbers figures in order of first use, so text can refer to a figure before it appears.

    figs = Figures()
    f"... as shown in {figs.ref('joint')} ..."
    figs.add("joint", "joint.svg", "Joint assembly, three steps.")
    """

    def __init__(self, label: str = "Figura") -> None:
        self.label = label
        self._numbers: dict[str, int] = {}

    def number(self, key: str) -> int:
        return self._numbers.setdefault(key, len(self._numbers) + 1)

    def ref(self, key: str) -> str:
        return f"{self.label} {self.number(key)}"

    def add(self, key: str, svg: str | Path, caption: str, *, width: str = "100%") -> str:
        """HTML for one figure. The SVG goes in as a data URI, so ids and fonts cannot clash with the page."""
        raw = Path(svg).read_text(encoding="utf-8")
        found = re.search(r"<desc>(.*?)</desc>", raw, re.DOTALL) or re.search(r"<title>(.*?)</title>", raw, re.DOTALL)
        alt = found.group(1) if found else caption
        data = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        return (
            f'<figure style="margin:0 0 4mm;break-inside:avoid-page">'
            f'<img src="data:image/svg+xml;base64,{data}" alt="{escape(alt, quote=True)}" '
            f'style="display:block;width:{width};height:auto;margin:0 auto">'
            f'<figcaption style="margin-top:1.5mm;font-size:.9em"><b>{self.ref(key)}.</b> {escape(caption)}</figcaption>'
            "</figure>"
        )
