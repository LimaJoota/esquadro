# Sketch mode: strokes and printing

How to choose the form, and the tools for explaining, are in `references/explaining.md`. This page is about the strokes themselves.

A sketch says "this is the idea, not the final design". It does not excuse wrong proportions. When the same object needs both a sketch and a technical sheet, one `draw(view)` function can serve both modes: see `examples/cargo_section.py`.

```python
d = Drawing(180, 120, "sketch", title="...", seed=7, wobble="pencil")
```

## The line

Each stroke is a thin filled ribbon, not an SVG stroke, so its width and tone change along it: pressure varies, the ends taper, and a firm line sometimes gets a partial second pass. A filter adds what the paper does: the edge frays, fine grain breaks the line, and tone drifts along its length. Lettering gets a lighter version, to stay readable. Always check it up close: `render.py out.svg close.png --dpi 500 --zoom x,y,w,h`.

| `wobble` | How | Best for |
|---|---|---|
| `"pencil"` (default) | Ribbons with the grain filter | Browser, HTML, PNG, PDF |
| `"geometry"` | The same ribbons, with no filter: smooth edges, stays fully vector | Inkscape, office programs, enlarging a lot |
| `"none"` | Straight, even strokes with the handwritten font | Very small figures |

`seed` makes the result repeatable. Change it if a stroke lands badly.

Washes follow the same split: `wash="filter"` bleeds and pools, and `wash="flat"` is a plain translucent shape. They default to `flat` when `wobble="geometry"`.

In Chrome's PDF the filters turn lines, letters and washes into images, at about 290 dpi in testing, so the text cannot be selected and it will not enlarge cleanly past that. Other renderers were not tested: see `BACKLOG.md`.

## What makes a sketch read well

- Fewer lines than the technical version: leave out what the sketch is not about.
- Corners overshoot a little on `rect` and `polygon`, as a hand with a ruler does. Use `polyline` for connected curves.
- Show the numbers that carry the decision and leave the rest out.
- Heavy hatching at small scale turns to black: raise `spacing`.
- Keep the note "SEM ESCALA" unless the view really has a scale.
- Text sizes: `"dim"`, `"label"`, `"heading"`, `"title"`, or a number in mm. The handwritten font runs smaller than the technical one, so these are already larger in this mode.
