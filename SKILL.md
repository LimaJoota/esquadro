---
name: esquadro
description: Draw hand-style sketches that explain things, and technical figures for documents, as checked, print-ready SVG. Use whenever a drawing would help someone understand, even if nobody asks for one by that name, or when the user says "desenha", "faz um desenho", "faz um croqui", "esboço", "esquema", "ilustra", "explica com desenho", "mostra como funciona", "passo a passo com figura", "figura para o relatório", "draw this", "sketch" or "illustrate". Covers how something is arranged, how to do it, right versus wrong, who does what, and also dimensioned sections, sheets with a title block, load arrangements and simplified process flows. Also use it to check an existing SVG for overlapping text, lines through labels or elements off the page. Not for software architecture or sequence diagrams, data charts, photos or artistic illustration.
license: MIT
metadata:
  version: "0.3.0"
---

# Esquadro

Sketches that explain, and technical figures that support a document. Decide what the reader must understand, draw it, check it, look at it. A drawing is delivered only after all of that.

Sketch is the default. Reach for `technical` mode only when the drawing will be used to measure or build, or the user asks for it.

`<skill>` below is this skill's base directory. The library uses only the Python standard library. Rendering and the most accurate text check use a local Chrome, Chromium or Edge.

## Workflow

1. **Write the sentence**: the one thing the reader should get from the figure. Then read `references/explaining.md` and pick the form that says it: arrangement, steps, right versus wrong, flow, or cut.
2. **Draw** with the library, in a script saved beside the output, so the drawing can be changed and regenerated. Hand-placed SVG is where labels land on top of each other.
3. **Validate**: `python3 <skill>/scripts/validate.py out.svg`. Fix every error at its cause in the script, and read the warnings.
4. **Render and look**: `python3 <skill>/scripts/render.py out.svg out.png`, then open the PNG with the Read tool. Ask whether it says the sentence to someone who has not read the text. The validator cannot judge that, nor a leader running through an object. Cover the numbers with your hand: can each part still be recognised by its shape? If a float is just a circle on a stick, draw it better before delivering.
5. **Check black and white** when it will be printed: `render.py out.svg gray.png --gray`.
6. **Deliver** the SVG, the PNG and the script. Say what was assumed, and what was not verified.

Repeat 3 and 4 after every change. If the validator reports text measured by `static` because no browser was found, say so: widths were estimated.

## Modes

| Mode | Use for | Look |
|---|---|---|
| `sketch` (default) | Explaining: reports, meetings, manuals, ideas | Pencil tremor on the strokes, handwritten font |
| `technical` | Parts, sections, arrangements, sheets with a title block | Clean strokes, thick and thin line weights |
| `industrial` | Process flows, simplified P&IDs | Technical look, with process symbols |

## Example: a sketch that explains

```python
import sys
sys.path.insert(0, "<skill>/scripts")
from esquadro import Drawing, Iso, callout, hand_note, legend

d = Drawing.figure("page", 80, lang="pt", title="Tanque e bomba", description="Tanque ligado a uma bomba, com chamadas.")
d.text((5, 9), "Tanque e bomba", "heading")
iso = Iso(d, (15, 62), unit=0.55)
tank = iso.cylinder((20, 30, 0), (20, 30, 50), 14)      # far objects first
iso.cylinder((34, 30, 8), (52, 30, 8), 2, shade=False)
pump = iso.box(52, 22, 0, 14, 16, 14)
callout(d, tank["side"], 1, (62, 24))
callout(d, pump["top"], 2, (76, 46))
legend(d, 92, 18, ["Tanque: guarda a água.", "Bomba: empurra a água para a rede."], 72)
hand_note(d, pump["right"], (92, 58), "fica perto do tanque para puxar com folga", 60, size=3.8)
d.save("explica.svg")
```

Write every word in the drawing in the language of the request, and pass `lang="pt"` or `"en"`: it sets the printed notices and the decimal separator. `Drawing.figure("page", h)` is 170 mm wide and `"half"` is 80 mm, to fit a document at true size. `finish="napkin"`, `"study"` or `"clean"` sets how loose the hand is. It prints "NOT TO SCALE" by itself.

**Colour is optional, and pencil is the base.** Add it when it carries meaning:

- Pen: `ink="red"` for the problem or the point of attention, `ink="blue"` for the correct way or a calm note. Every explaining tool takes `ink=`, and `with d.pen("red"):` covers anything else.
- Watercolour: `iso.cylinder(..., color="blue")`, `iso.box(..., color="yellow")`, or `d.wash(points, "blue")` after an outline and before its hatching. Colours: `blue`, `red`, `yellow`, `green`, `brown`, `gray`.
- Colour must never be the only signal. A printer in black and white turns red and blue into grays, so a right or wrong keeps its shape (`mark`), and text says what the colour means. Check with `--gray`. For a print-only document, stay in pencil.

## Example: a technical sheet

```python
import sys
sys.path.insert(0, "<skill>/scripts")
from esquadro import Drawing, Scale

LENGTH, HEIGHT = 2400.0, 600.0                      # real millimetres, named once

d = Drawing.sheet("A3", title="Viga de apoio", lang="pt", title_block={"number": "D-01", "drawn": "Projetista", "date": "2026-11-04"})
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

Use `d.view(origin, Scale(1, 50))` to place a view yourself, and `Scale.schematic(factor)` when the proportions are only indicative.

## Rules that keep drawings right

**Scale is declared or disclaimed.** A view has a real scale, or the drawing says "SEM ESCALA" / "NOT TO SCALE". The library prints this by itself. Pick from the standard series. If a scale does not fit, `fit_view` raises an error: change the sheet or the scale, do not squeeze.

**Dimensions come from geometry.** `dim_h`, `dim_v`, `dim_aligned`, `dim_diameter` and `dim_radius` measure the points you pass, in real units, through the view's scale. Passing `value=` that disagrees raises `DimensionMismatch`. When a value truly cannot match, as across a broken view, pass `nts=True`: the value is underlined, the usual mark for "not to scale".

**A sketch does not need measurements, and must not invent them.** Rough sizes go in `span(d, a, b, "≈ 2 m")`. When real numbers matter and you do not have them, ask, or mark each assumed number as assumed. Say so plainly when a figure looks authoritative but rests on guesses.

**A drawing makes claims.** An explanation of how something works, or which way is right, can be wrong however good it looks. If you are unsure of the content, tell the user rather than illustrating it confidently.

**Text goes in free space.** Never `dominant-baseline`, never a stroke through a label. Use `d.note` for leaders, `d.notes` and `d.paragraph` for wrapped text and `d.table` for tables, because they measure text with the embedded font. Use `knockout=True` only for text that must sit on hatching.

**Black and white first.** Tell lines apart by weight and dash, never by color alone. Hatching is real clipped lines.

**The standards are guides here, not certification.** Read `references/standards.md` before claiming conformity to anything. Standards are paid documents: apply conventions, never quote their text. Where a project demands strict conformity, tell the user the drawing must be reviewed against the standard itself.

## Reference, read when needed

- `references/explaining.md`: read for every explanatory sketch. How to choose the form, and all the tools.
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

Warnings: `LEADER_CROSS`, `TEXT_ON_WASH_EDGE`, `SMALL_TEXT`, `THIN_STROKE`, `LOW_CONTRAST`, `COLOR_ONLY`, `FONT_NOT_EMBEDDED`, `TEXT_ESTIMATED`, `NONSTANDARD_SCALE`. Options: `--strict`, `--json`, `--static`, `--margin N`, `--annotate out.svg`, which rings each error in red so you can look at it.

## Embedding

The SVG carries its own font and needs nothing else. For a document, `Figures` numbers the figures and gives cross-references: see `references/explaining.md`. In HTML, `<img src="x.svg">` or inline both work. For PDF, `render.py out.svg out.pdf` writes the true paper size. Technical drawings stay fully vector. Sketch mode's filter is rasterized by Chrome's PDF engine, at about 270 dpi in testing, with text still vector. Use `Drawing(..., wobble="geometry")` when the strokes must stay vector, or for programs that ignore SVG filters; washes then become flat translucent fills. `wash="flat"` does that for washes alone.
