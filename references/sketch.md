# Sketch mode: strokes and printing

How to choose the form, and the tools for explaining, are in `references/explaining.md`. This page is about the strokes themselves.

A sketch says "this is the idea, not the final design". It does not excuse wrong proportions. When the same object needs both a sketch and a technical sheet, one `draw(view)` function can serve both modes: see `examples/cargo_section.py`.

```python
d = Drawing(180, 120, "sketch", title="...", seed=7, wobble="filter")
```

## Tremor

| `wobble` | How | Best for |
|---|---|---|
| `"filter"` (default) | `feTurbulence` + `feDisplacementMap` over the stroke groups; text stays crisp | Browser, HTML, PNG |
| `"geometry"` | Strokes are computed with small random deviations and stay plain paths | PDF that must be fully vector, Inkscape, office programs |
| `"none"` | Straight strokes with the handwritten font | Very small figures |

`seed` makes the result repeatable. Change it if a stroke lands badly.

In Chrome's PDF the filter turns the strokes into an image, about 270 dpi on a figure 230 mm wide in testing, with the text still vector. That prints well but will not scale up. Other renderers were not tested: see `BACKLOG.md`.

## What makes a sketch read well

- Fewer lines than the technical version: leave out what the sketch is not about.
- Corners overshoot a little on `rect` and `polygon`, as a hand with a ruler does. Use `polyline` for connected curves.
- Show the numbers that carry the decision and leave the rest out.
- Heavy hatching at small scale turns to black: raise `spacing`.
- Keep the note "SEM ESCALA" unless the view really has a scale.
- Text sizes: `"dim"`, `"label"`, `"heading"`, `"title"`, or a number in mm. The handwritten font runs smaller than the technical one, so these are already larger in this mode.
