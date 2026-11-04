---
name: esquadro
description: Draw engineering, industrial and corporate figures as checked, print-ready SVG, with real scale and computed dimensions. Use whenever the user wants a technical drawing, cross-section, dimensioned part, load or cargo arrangement, pipe or tank sketch, process flow or simplified P&ID, equipment or layout figure, or a pencil-style sketch for a report or meeting, even if they just say "desenha", "faz um desenho", "croqui", "esboço", "corte", "vista", "planta", "cota", "esquema", "draw this", "sketch" or "section view". Also use it to check an existing SVG for overlapping text, lines through labels or elements off the page. Not for software architecture or sequence diagrams, data charts, photos or artistic illustration.
license: MIT
metadata:
  version: "0.1.0"
---

# Esquadro

Draw by calculating, then check, then look. A drawing is delivered only after all three.

Hand-placed coordinates are where drawings go wrong: labels land on top of each other, a dimension says one thing while the geometry says another, and nobody notices until it is printed. So geometry comes from a script, dimension text comes from that geometry, and the result is checked by a validator and by your own eyes.

`<skill>` below is this skill's base directory. The library uses only the Python standard library. Rendering and the most accurate text check use a local Chrome, Chromium or Edge.

## Workflow

1. **Pick the mode** (table below) and write the real measurements down as named parameters at the top of a Python script. Derive everything else from them.
2. **Draw** with the library, in a script saved beside the output so the drawing can be regenerated.
3. **Validate**: `python3 <skill>/scripts/validate.py out.svg`. Fix every error at its cause in the script.
4. **Render and look**: `python3 <skill>/scripts/render.py out.svg out.png`, then open the PNG with the Read tool. The validator cannot judge whether a leader crosses a dimension, a view is cramped or the drawing is simply wrong.
5. **Check black and white** when it will be printed: `render.py out.svg gray.png --gray`.
6. **Deliver** the SVG, the PNG and the script. Say what was calculated, what was assumed, and what was not verified.

Repeat 3 and 4 after every change. If the validator reports text measured by `static` because no browser was found, say so: widths were estimated.

## Modes

| Mode | Use for | Look |
|---|---|---|
| `technical` | Parts, sections, arrangements, sheets with a title block | Clean strokes, thick and thin line weights, sans lettering |
| `sketch` | Reports, meetings, early ideas | Pencil tremor on the strokes, handwritten font |
| `industrial` | Process flows, simplified P&IDs | Technical look, with process symbols |

## Example

```python
import sys
sys.path.insert(0, "<skill>/scripts")
from esquadro import Drawing, Scale

LENGTH, HEIGHT = 2400.0, 600.0                      # real millimetres, named once

d = Drawing.sheet("A3", title="Viga de apoio", title_block={"number": "D-01", "drawn": "Projetista", "date": "2026-11-04"})
v = d.fit_view((0, 0, LENGTH, HEIGHT), pad=(30, 20, 30, 30))   # picks the largest standard scale that fits
v.rect(0, 0, LENGTH, HEIGHT)
v.hatch([(0, 0), (300, 0), (300, HEIGHT), (0, HEIGHT)])
v.centerline((0, HEIGHT / 2), (LENGTH, HEIGHT / 2))
v.dim_h((0, 0), (LENGTH, 0), side="bottom")         # the text "2400" comes from these points
v.dim_v((LENGTH, 0), (LENGTH, HEIGHT), side="right")
v.note((300, HEIGHT), (10, -12), "Região cortada")
d.notes(250, 40, ["Cotas em milímetros."], 150, heading="NOTAS")
d.save("viga.svg")
```

For a figure without a sheet: `Drawing(180, 120, "sketch", title="...")`. Use `d.view(origin, Scale(1, 50))` to place a view yourself, and `Scale.schematic(factor)` when the proportions are only indicative.

## Rules that keep drawings right

**Scale is declared or disclaimed.** A view has a real scale, or the drawing says "SEM ESCALA" / "NOT TO SCALE". The library prints this by itself. Pick from the standard series. If a scale does not fit, `fit_view` raises an error: change the sheet or the scale, do not squeeze.

**Dimensions come from geometry.** `dim_h`, `dim_v`, `dim_aligned`, `dim_diameter` and `dim_radius` measure the points you pass, in real units, through the view's scale. Passing `value=` that disagrees raises `DimensionMismatch`. When a value truly cannot match, as across a broken view, pass `nts=True`: the value is underlined, the usual mark for "not to scale".

**Do not invent measurements.** Ask, or draw a schematic and mark each assumed number as assumed. Say so plainly when a figure looks authoritative but rests on guesses.

**Text goes in free space.** Never `dominant-baseline`, never a stroke through a label. Use `d.note` for leaders, `d.notes` and `d.paragraph` for wrapped text and `d.table` for tables, because they measure text with the embedded font. Use `knockout=True` only for text that must sit on hatching.

**Black and white first.** Tell lines apart by weight and dash, never by color alone. Hatching is real clipped lines.

**The standards are guides here, not certification.** Read `references/standards.md` before claiming conformity to anything. Standards are paid documents: apply conventions, never quote their text. Where a project demands strict conformity, tell the user the drawing must be reviewed against the standard itself.

## Reference, read when needed

- `references/technical.md`: sheets, views, sections, hatching, dimensions, full API.
- `references/sketch.md`: sketch mode, tremor options, what prints well in PDF.
- `references/industrial.md`: process symbols, connections, limits of the P&ID support.
- `references/standards.md`: which conventions are applied, their sources, which Brazilian standards were replaced, open doubts.
- `examples/`: complete scripts with their SVG and PNG output.

## Validator

`validate.py` works on any SVG, including hand-written ones. Errors exit with code 1.

| Code | Means | Usual fix |
|---|---|---|
| `TEXT_OVERLAP` | Two texts overlap | Move one; `shift=` slides a dimension value along its line |
| `TEXT_CROSSED` | A stroke runs through text | Increase `offset`, use `tail=` on a diameter, or reposition the leader |
| `OUT_OF_BOUNDS` | Leaves the canvas, or the sheet frame | Adjust `pad`, the area or the scale |
| `DIM_MISMATCH` | Printed value disagrees with geometry and scale | Regenerate instead of editing the SVG |
| `DIM_NTS_MARK` | Not-to-scale value without its underline | Regenerate with `nts=True` |
| `NO_SCALE` | No scale and no "not to scale" notice | Print one |
| `EXTERNAL_REF` | Script or external file | Remove it: the SVG must stand alone |

Warnings: `SMALL_TEXT`, `THIN_STROKE`, `LOW_CONTRAST`, `COLOR_ONLY`, `FONT_NOT_EMBEDDED`, `TEXT_ESTIMATED`, `NONSTANDARD_SCALE`. Options: `--strict`, `--json`, `--static`, `--margin N`, `--annotate out.svg`, which rings each error in red so you can look at it.

## Embedding

The SVG carries its own font and needs nothing else. In HTML, `<img src="x.svg">` or inline both work. For PDF, `render.py out.svg out.pdf` writes the true paper size. Technical drawings stay fully vector. Sketch mode's filter is rasterized by Chrome's PDF engine, at about 270 dpi in testing, with text still vector. Use `Drawing(..., wobble="geometry")` when the strokes must stay vector, or for programs that ignore SVG filters.
