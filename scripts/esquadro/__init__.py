"""Esquadro: explanatory sketches and technical drawings as checked, self-contained SVG."""

from . import symbols
from .core import PAPER, VERSION, Drawing, Scale, format_value, hatch_segments, text_width
from .document import Figures
from .explain import Panel, callout, flow_arrow, hand_note, legend, mark, marker, panels, ring, span
from .objects import Iso, building, document, person, truck
from .view import DimensionMismatch, View

__all__ = [
    "PAPER",
    "VERSION",
    "DimensionMismatch",
    "Drawing",
    "Figures",
    "Iso",
    "Panel",
    "Scale",
    "View",
    "building",
    "callout",
    "document",
    "flow_arrow",
    "format_value",
    "hand_note",
    "hatch_segments",
    "legend",
    "mark",
    "marker",
    "panels",
    "person",
    "ring",
    "span",
    "symbols",
    "text_width",
    "truck",
]
