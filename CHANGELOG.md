# Changelog

## 0.3.0

- Pen colours: `ink="red"` and `ink="blue"` on the explaining tools, and `with d.pen(...)` for anything else.
- Watercolour: `d.wash()`, `iso.box(color=)` and `iso.cylinder(color=)`, with bleeding edges and pooled pigment. `wash="flat"` for programs that ignore SVG filters.
- Validator: translucent fills no longer count as hiding a stroke behind text; new `TEXT_ON_WASH_EDGE` warning.
- English versions of the explanatory examples.
- Plugin marketplace manifest and continuous integration.
- Drawings now default to English; pass `lang="pt"` for Portuguese. The skill matches the language of the request.
- Browser text measurement no longer fails silently on empty text elements.

## 0.2.0

- Explanatory sketches became the centre of the skill.
- Numbered callouts and legends, hand notes, panels, right and wrong marks, free spans, emphasis loops, finish levels.
- Isometric boxes and cylinders with hand shading, plus person, truck, building and document.
- `Figures` for numbered figures and cross-references in documents.
- Validator: `LEADER_CROSS` warning.

## 0.1.0

- Technical, sketch and industrial modes, sheets with title block, dimensions computed from geometry.
- Validator for any SVG, and rendering through a local browser.
