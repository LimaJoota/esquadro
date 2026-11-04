# Industrial mode

Read this for process flows and simplified P&IDs.

**Limit of v0.1:** a small, simplified symbol set in the general style of ISA-5.1 and ISO 10628. It has not been checked against those standards, which are paid. Good for explaining a process, not for issuing a P&ID for construction. Say so when delivering. `BACKLOG.md` has the plan for full libraries.

```python
from esquadro import Drawing
from esquadro.symbols import box, exchanger, instrument, pipe, pump, valve, vessel

d = Drawing.sheet("A3", mode="industrial", title="...", title_block={"projection": None})
```

Symbols work in paper millimetres and return an item with named ports. Connect ports, not coordinates.

| Function | Ports |
|---|---|
| `vessel(d, at, w, h, tag, label)` | `left right top bottom left_low right_low left_high right_high` |
| `pump(d, at, tag, label)` | `in out` |
| `valve(d, at, tag, vertical=False, actuator=False)` | `in out`, and `actuator` |
| `exchanger(d, at, tag, label, r=8, tag_offset=0)` | `in out shell_in shell_out` |
| `instrument(d, at, "FIC", "101", location="panel")` | `left right top bottom` |
| `box(d, at, w, h, ["Line 1", "Line 2"])` | `left right top bottom` |

`pipe(d, a, b, route="auto", kind="visible", arrow=True, label=None, label_side="top", arrow_at=None, label_at=0.5)`

- `route`: `h`, `v`, `hv`, `vh`, `hvh`, `vhv`, or `auto`.
- `kind`: `visible` for process lines, `thin` for utilities and instrument tappings, `signal` for instrument signals.

## Working method

- Lay symbols out by columns computed from the area, so the whole train moves together. See `examples/process_flow.py`.
- Put symbols that connect in a straight line on the same y, derived from the port: `pump(d, (x, tank.port("right_low")[1]), ...)`.
- Flow runs left to right. Use `hvh` for level changes.
- Check for crossings while looking at the PNG: pipes crossing pipes are not flagged by the validator, and line jumps do not exist yet. Route around, or stop a utility line short and label it, as with "Vapor" in the example.
- Put calculated values, such as heat duty or flow, in a table marked `calculado` or `parâmetro`, so the reader knows which is which.
- Instrument letters follow the usual first-letter and function logic: `TI` temperature indicator, `FT` flow transmitter, `FIC` flow indicating controller, `LT` level transmitter. `location="panel"` adds the middle line of a panel-mounted device.
