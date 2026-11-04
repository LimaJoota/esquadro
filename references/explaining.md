# Explaining with a sketch

Read this before drawing anything meant to explain. Most of the value is decided before the first stroke.

## Start with the sentence

Write down the one thing the reader should understand after looking: "the socket is what seals, and the mark says when to stop". If it takes two sentences, it is two figures. Everything in the drawing either supports that sentence or comes out.

## Pick the form

| The reader needs to understand | Use | Example |
|---|---|---|
| How something is arranged, and what each part does | Volumes in perspective, numbered callouts, legend | `explain_system.py` |
| How to do something, in order | Panels, 3 or 4 frames | `explain_steps.py` |
| Why one way is better than another | Two panels with right and wrong marks | `explain_compare.py` |
| What happens to what, who does what | People and objects along a line, arrows | `explain_flow.py` |
| What is inside, or why it works | Cut, then hand notes on the parts that matter | `explain_cut.py` |
| A precise measure that will be used | Not a sketch: `technical` mode | `cargo_section.py` |

## Rules of thumb

- **Omit generously.** Draw only what the sentence needs. No wall thickness unless thickness is the point.
- **One emphasis per figure.** `ring` around the part that matters, or a bolder line, once.
- **Notes say why, not what.** "Nothing holds the end pipe" beats "pipe".
- **Up to about 7 callouts.** If there are more, split the figure.
- **Proportion is honest even without scale.** A pump as tall as the tank tells the reader something false. Rough sizes go in `span` with "≈".
- **Use the reader's words.** Same language and vocabulary as the document it goes in. Portuguese drawings get `lang="pt"`, the default.
- **Say what is assumed.** An example of how a thing works can carry a claim. If you are not sure the claim is true, say so to the user or take it out of the drawing.

## Tools

All in paper millimetres. Import from `esquadro`.

```text
callout(d, target, n, at)            numbered marker with a line to a dot on the target
legend(d, x, y, items, width)        numbered explanations; returns the y below
marker(d, at, n)                     number in a circle, alone
hand_note(d, target, at, text, width, bend=0.22, size="label")
                                     wrapped note at `at` (its top-left), curved arrow to the target
span(d, a, b, "≈ 2 m")               double arrow with free text; measures nothing
ring(d, center, rx, ry)              loose loop around what matters
mark(d, at, ok)                      heavy check or cross
flow_arrow(d, a, b, bend=0, label=None)
panels(d, n, area=, titles=, verdicts=, arrows=True, gap=14)
                                     row of frames; each has x, y, w, h and at(fx, fy)
```

Objects, sizes indicative:

```text
iso = Iso(d, origin, unit=0.6)       x runs lower right, y upper right, z up; iso.p(x, y, z) gives a paper point
iso.box(x, y, z, w, depth, h, shade="right")      returns top, left, right, base points
iso.cylinder(a, b, r, shade=True)    any direction; returns near, far, side points
iso.shadow(x, y, w, depth)           hatched patch on the ground; draw it first
person(d, feet, h=24, arm="out")     returns head, hand
truck(d, at, length=70)              returns bed = (x1, x2, y), to load things on
building(d, at, w, h)                returns top, left, right
document(d, at, w, h)                returns left, right, top, bottom
```

`esquadro.symbols` (`vessel`, `pump`, `valve`, `exchanger`) also works in sketch mode.

## Method

1. Place from the far objects to the near ones: later solids cover earlier ones. Painting order is yours.
2. Attach notes and callouts to the points the objects return, not to typed coordinates, so they follow if the drawing moves.
3. Place markers in clear space around the drawing, with leaders that do not cross. `LEADER_CROSS` warns about crossings with other leaders and with dimensions.
4. Render and look. Does the drawing say the sentence from step one, to someone who has not read the text? The validator cannot tell you that, and a leader running through a person's head passes it.

## Finish

`Drawing.figure("page", 90, finish="study")`

| `finish` | Looks | Use for |
|---|---|---|
| `"napkin"` | Loose, more tremor, longer overshoot | "Here is a rough idea" |
| `"study"` | The default | Reports and meetings |
| `"clean"` | Barely trembling | Formal documents that still want a human feel |

## In a document

`Drawing.figure("page", h)` is 170 mm wide, `"half"` is 80 mm: the A4 text width and half of it, printed at true size. Text keeps its height, so do not scale the figure in the page, or size it there and make it again.

```python
from esquadro import Figures

figs = Figures()
paragraph = f"A junta tem três passos, mostrados na {figs.ref('joint')}."
html = figs.add("joint", "explain_steps.svg", "Montagem da junta.")
```

Numbers follow the order of first use, so text can cite a figure before it appears. The SVG goes in as a data URI, with the `<desc>` as alt text, so the HTML stands alone. Give every drawing a `description=` for that.
