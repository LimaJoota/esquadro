"""Esquadro: engineering, industrial and sketch drawings as checked, self-contained SVG."""

from . import symbols
from .core import PAPER, VERSION, Drawing, Scale, format_value, hatch_segments, text_width
from .view import DimensionMismatch, View

__all__ = [
    "PAPER",
    "VERSION",
    "DimensionMismatch",
    "Drawing",
    "Scale",
    "View",
    "format_value",
    "hatch_segments",
    "symbols",
    "text_width",
]
