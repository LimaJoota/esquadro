# Esquadro

A [Claude Code](https://claude.com/claude-code) skill for engineering, industrial and sketch drawings: self-contained SVG with real scale, dimensions computed from the geometry, and a validator that catches what goes wrong in drawn-by-hand SVG.

*Esquadro* is Portuguese for a drafting set square.

> **Em português:** skill para desenho técnico, industrial e croqui. Gera SVG sem dependências, que imprime bem em preto e branco, com escala declarada e cotas calculadas da própria geometria. O validador pega texto sobre texto, traço cruzando texto e elemento fora da folha, e a skill manda sempre renderizar e olhar antes de entregar. Instale com o comando abaixo e peça "desenha o corte de...". Versão inicial: as convenções de norma são aplicadas a partir de material aberto e não são certificação. Veja [BACKLOG.md](BACKLOG.md) (em português) e [references/standards.md](references/standards.md).

## Install

```bash
git clone https://github.com/LimaJoota/esquadro ~/.claude/skills/esquadro
```

Then ask Claude to draw something: *"draw a dimensioned section of a flatbed trailer carrying six 800 mm pipes"* or *"faz um croqui do tubo corrugado com bolsa para o relatório"*.

Needs Python 3.10 or later, standard library only. Tested on 3.14. Rendering and the most accurate text check use a local Chrome, Chromium or Edge. Without one, the validator falls back to bundled font metrics and says so.

## Before and after

An SVG written by hand has the faults you would expect, and they are easy to miss in the code. Here the validator's `--annotate` option has ringed them:

![A hand-written SVG with overlapping labels and text running off the page, the errors ringed in red](examples/before_after/naive_cargo_annotated.png)

```text
ERROR   TEXT_OVERLAP       "Pipe OD 800 mm" overlaps "Pipe OD 800 mm"
ERROR   TEXT_CROSSED       circle crosses "Load section on semi-trailer" near (142.8, 22.0)
ERROR   TEXT_CROSSED       line crosses "Deck width 2600 mm" near (280.0, 390.1)
ERROR   OUT_OF_BOUNDS      line extends to (519.5, -12.5)-(520.5, 284.5) on a 640x420 canvas
ERROR   NO_SCALE           no scale printed and no "sem escala / not to scale" notice; a reader will measure it
FAIL naive_cargo.svg: 12 errors, 1 warnings (7 texts, 13 shapes, text measured by browser)
```

The same subject from a script, where each height is calculated from the pipe diameter and stacking pattern:

![The same load as a technical sheet: section at 1:20, dimensions, data table and title block](examples/cargo_section_technical.png)

## Examples

Each script in [`examples/`](examples) is complete, with its SVG and PNG alongside. All content is generic and illustrative.

| Technical or industrial | Sketch |
|---|---|
| ![Cargo section, technical](examples/cargo_section_technical.png) | ![Cargo section, sketch](examples/cargo_section_sketch.png) |
| ![Corrugated pipe with socket, half section and profile detail](examples/corrugated_pipe_technical.png) | ![Corrugated pipe, sketch](examples/corrugated_pipe_sketch.png) |
| ![Process flow with vessels, pump, heater and instruments](examples/process_flow_technical.png) | ![Process flow, sketch](examples/process_flow_sketch.png) |

## What it does

- **Three modes.** `technical`: clean strokes, thick and thin line weights, sheets with frame and title block, first-angle symbol. `sketch`: pencil tremor with SVG filters or computed strokes, plus a handwritten font. `industrial`: a small set of process symbols with named ports and orthogonal connections.
- **Dimensions from geometry.** A dimension measures the points it is given, through the view's scale. A stated value that disagrees raises an error unless it is marked not to scale, which underlines it. The validator re-checks printed numbers against the drawn lines, so a hand edit is caught too.
- **Scale is declared or disclaimed.** The largest standard ratio that fits is chosen by calculation, or the drawing prints "SEM ESCALA" / "NOT TO SCALE".
- **Self-contained output.** The font is embedded as a subset. There are no scripts or external files, and hatching is real clipped lines. It works inline in HTML, through `<img>`, and through Chrome's PDF.
- **A validator for any SVG**, hand-written ones included: overlapping text, strokes through text, elements off the page or sheet frame, external references, missing scale, small or faint text, colors that look alike in black and white. It handles nested transforms, `<use>`, tspans, simple CSS and all path commands, and measures text with a real browser when it can.
- **A method.** The skill tells Claude to calculate, validate, render and look at the image before delivering, and to say what was assumed.

```bash
python3 scripts/validate.py drawing.svg --annotate ringed.svg
```

```bash
python3 scripts/render.py drawing.svg drawing.png --gray
```

## How it compares

Use the tool that fits. Licenses as checked on 2026-11-04.

| Project | Good at | When to prefer Esquadro |
|---|---|---|
| [draw.io skill](https://github.com/jgraph/drawio-mcp) (Apache-2.0) | Editable diagrams with large symbol libraries | Scale, computed dimensions, checked output. Prefer draw.io when people must edit by hand |
| [Excalidraw skill](https://github.com/coleam00/excalidraw-diagram-skill) (no license file) | Whiteboard-style diagrams | Measured drawings, printing |
| [tldraw](https://github.com/tldraw/tldraw) (own license) | Canvas SDK for apps | Static files, no app |
| [archify](https://github.com/tt-a1i/archify) (Apache-2.0) | Software architecture and flow diagrams as interactive HTML | Physical objects. Use archify for systems |
| [Prancheta](https://github.com/JoaoVictor-C/Prancheta) (MIT) | General figures with a render, inspect and repair loop; the closest in spirit | Drafting conventions: scale, sheets, dimensions, sections |
| [CadQuery](https://github.com/CadQuery/cadquery) (Apache-2.0), [FreeCAD](https://github.com/FreeCAD/FreeCAD) (LGPL-2.1), [OpenSCAD](https://github.com/openscad/openscad) (GPL) | True 3D solids and manufacturing data | Annotated 2D figures for documents. Use these when the 3D model matters |
| [schemdraw](https://github.com/cdelker/schemdraw) (MIT) | Electrical schematics in Python | Mechanical and process figures. Use it for circuits |
| [rough.js](https://github.com/rough-stuff/rough) (MIT) | Hand-drawn graphics in JavaScript | No JavaScript at any stage, plus dimensioning |

Esquadro is younger and narrower than all of these. No code was copied from any of them.

## Limits, plainly

- **Not a CAD system.** It produces 2D figures from scripts, with no 3D model behind them and no DXF yet.
- **Not certified to any standard.** Conventions are applied from open sources, and doubts are recorded in [references/standards.md](references/standards.md). Review against the purchased standard when a contract asks for conformity.
- **Process symbols are simplified** and unverified against ISA-5.1 or ISO 10628. Not for issuing a P&ID.
- **Rendering tested in Chrome only.** Other browsers, Inkscape and office programs have not been tried.
- **In Chrome's PDF the sketch filter becomes an image** (about 270 dpi in testing). Text stays vector. `wobble="geometry"` keeps everything vector.
- **The validator misses things a person sees**, such as a leader crossing a dimension or a cramped layout. That is why the skill also makes Claude look.

The plan to close these is in [BACKLOG.md](BACKLOG.md).

## Development

```bash
pip install pytest && python3 -m pytest
```

```bash
python3 examples/build_all.py
```

## License

Code and examples: [MIT](LICENSE). Bundled fonts, under the SIL Open Font License 1.1 and subset for size: [Overpass](assets/fonts/OFL-overpass.txt) and [Patrick Hand](assets/fonts/OFL-patrick-hand.txt). Generated drawings embed these fonts, which the OFL allows. Your drawings are yours.
