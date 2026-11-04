# Technical mode

Read this when composing a sheet, a multi-view drawing, sections or dense dimensioning.

## Sheets and figures

```python
Drawing.sheet(size="A3", orientation="landscape", mode="technical",
              title_block={...}, frame="iso", title="...", lang="pt", seed=7)
Drawing(width_mm, height_mm, mode, title="...", description="...", lang="pt")
```

- `frame="iso"` uses margins of 20 mm left and 10 mm elsewhere. `frame="nbr-1987"` is the older Brazilian layout, only for projects that still ask for it.
- `title_block` keys: `number`, `drawn`, `date`, `rev`, `sheet`, `units`, `title`, `projection` (`"first"`, `"third"` or `None`).
- `d.area` is the free rectangle inside the frame and above the title block. The block occupies only the right side, so a view may use the free corner below `d.area` on the left: pass your own `area=(x, y, w, h)`.
- Long titles shrink to fit. Below the minimum size the library raises an error rather than overflow.
- `lang="en"` switches the printed words and the decimal separator. Portuguese uses a comma.

## Views

`d.fit_view(world, area=None, pad=(l, t, r, b), scale=None, main=True)`

- `world` is `(xmin, ymin, xmax, ymax)` in real millimetres, y up.
- `pad` is paper room reserved for dimensions and notes. Start with about 10 mm per row of dimensions.
- Without `scale`, it picks the largest ratio from the recommended series that fits. Passing one raises an error if it does not fit.
- Mark secondary views `main=False`. The title block shows the main view's scale, so give each secondary view a caption with `v.title(x, y, "DETALHE")`, which adds its own scale.

Line up views by sharing a coordinate. First-angle example, section left of the front view at the same height:

```python
front = d.fit_view(world, area=right_area, scale=Scale(1, 2))
section = d.view((95.0, front.origin[1]), front.scale, main=False)
```

## Geometry

All in world units through the view: `line`, `polyline`, `polygon`, `rect`, `circle`, `arc`, `centerline`, `center_mark`, `break_line`, `hatch`, `section_line`, `text`, `note`, `title`.

The same names on the `Drawing` work in paper millimetres, y down. Use them for notes, tables and anything not tied to the object.

Line kinds, passed as the last argument:

| Kind | Use |
|---|---|
| `visible` | Visible outlines, thick |
| `thin` | Dimensions, leaders, projection lines, short center marks |
| `hatch` | Section lines |
| `hidden` | Hidden edges, dashed |
| `center` | Axes and symmetry, chain |
| `phantom` | Adjacent parts, limits, alternative positions |
| `cutting` | Cutting planes |
| `border` | Sheet frame |
| `signal` | Instrument signals |

## Sections and hatching

- Close the outline with `polygon`, then hatch the same points: `v.hatch(points, spacing=1.2)`.
- Holes: pass several rings, `v.hatch([outer, inner])`. The fill rule is even-odd.
- Adjacent parts: change `angle` (`45`, `-45`) or `spacing`.
- Walls too thin to hatch at the chosen scale: fill solid with `polyline(pts, "thin", closed=True, fill="#000")`, and show a larger detail view if the wall matters.
- `spacing` is in paper mm, so it stays readable at any scale.
- `section_line(a, b, "A", look=(0, 1))` draws the cutting plane, thick ends, arrows and letters. Caption the section view `CORTE A-A`.

## Dimensions

```python
v.dim_h(a, b, side="bottom", offset=10)
v.dim_v(a, b, side="left", offset=10, prefix="Ø")
v.dim_aligned(a, b, offset=10)
v.dim_chain_h([x0, x1, x2], y, side="bottom", offset=10)
v.dim_diameter(center, d, angle=30, tail=None)
v.dim_radius(center, r, angle=45)
```

Common options: `value=`, `nts=True`, `prefix=`, `suffix=`, `decimals=`, `shift=` (slide the value along its line, in paper mm).

- `offset` is paper mm from the outermost measured point.
- Keep rows about 10 mm apart: shortest closest to the part, overall dimensions outermost, so extension lines do not cross values.
- When the value does not fit between the arrows, the library puts the arrows outside and the value beyond them.
- Vertical values read from the right-hand side of the sheet.
- Dimension each feature once, in the view that shows it best. Do not dimension to hidden lines if a section can show the edge.
- In a stack, the parts should add up to the overall: the numbers come from the same parameters, so write them that way.

## Layout checklist, while looking at the PNG

- Does any leader cross a dimension line or another leader? The validator does not catch this yet.
- Is the main view placed first and large enough? Would a bigger scale fit?
- Do views align by projection?
- Are the notes and tables away from the drawing, and is the white space even?
- Is every number a reader needs printed, and none repeated?

## Tables and notes

```python
d.table(x, y, rows, col_widths, row_height=7, align=("start", "end", "start"))
d.notes(x, y, ["First note.", "Second note."], width, heading="NOTAS")
d.paragraph((x, y), text, width)
```

These wrap and fit with the embedded font's metrics. Cell text below 2 mm raises an error.
